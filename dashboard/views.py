"""Storefront views — RGS TOWER."""

import re
from decimal import Decimal, InvalidOperation
from urllib.parse import quote, urlparse

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from . import discord_oauth, google_oauth, mailer, paypal
from .i18n import pick, t
from .middleware import COOKIE as LANG_COOKIE, COOKIE_AGE as LANG_COOKIE_AGE
from .i18n import LANGS
from .models import AboutPage, AboutStat
from .models import (
    Banner, Category, ContactMessage, Country, Coupon, CustomerProfile, HomeSection,
    Order, OrderItem, Policy, Product, ProductVariant, Review, Service, SiteSettings,
    TICKET_EXTS, TICKET_MAX_FILES, TICKET_MAX_FILE_MB, TICKET_STATUSES, TICKET_TOPICS,
    Ticket, TicketAttachment, TicketMessage, Work, WorkCategory, reviewable_orders, two_part_name,
    staff_permissions,
)
from .templatetags.store_tags import money as fmt_money
from .utils import Cart, money, save_ticket_attachments, ticket_uploads

PAGE_SIZE = 12
User = get_user_model()


def _dec(value, default=None):
    try:
        return Decimal(str(value))
    except (TypeError, ValueError, InvalidOperation):
        return default


def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _safe_next(request, fallback='home'):
    target = request.POST.get('next') or request.GET.get('next') or ''
    if target and url_has_allowed_host_and_scheme(target, {request.get_host()}, request.is_secure()):
        return target
    return reverse(fallback) if not fallback.startswith('/') else fallback


def normalize_phone(value):
    """Keep digits only; +20 / 0020 become a local 0 prefix."""
    digits = re.sub(r'\D', '', value or '')
    if digits.startswith('0020'):
        digits = '0' + digits[4:]
    elif digits.startswith('20') and len(digits) == 12:
        digits = '0' + digits[2:]
    return digits


def valid_phone(phone):
    """International numbers: 8–15 digits (E.164). Egyptian +20 numbers are kept as 01…"""
    return 8 <= len(phone or '') <= 15


def _sort_name(text):
    text = (text or '').strip().lower()
    for a in 'أإآ':
        text = text.replace(a, 'ا')
    return text


def shipping_countries(include=None):
    """Countries open for shipping, in the order the owner set, then by name.

    `include` keeps a customer's saved country in the list even if it was switched off.
    """
    countries = list(Country.objects.filter(is_active=True))
    if include is not None and include.pk not in {c.pk for c in countries}:
        countries.append(include)
    countries.sort(key=lambda c: (c.ordering, _sort_name(c.name)))
    return countries


def _saved_country(request):
    """The shopper's saved country while it is still open for shipping."""
    user = request.user
    if not user.is_authenticated:
        return None
    profile = getattr(user, 'customer', None)
    country = profile.country if profile else None
    return country if country is not None and country.is_active else None


def _base_products():
    return (
        Product.objects.filter(is_active=True)
        .select_related('category')
        .prefetch_related('images', 'colors', 'variants')
    )


# =================================================================== language
def set_language(request, code):
    code = code if code in LANGS else 'ar'
    target = request.GET.get('next') or request.META.get('HTTP_REFERER') or '/'
    if not url_has_allowed_host_and_scheme(target, {request.get_host()}, request.is_secure()):
        target = '/'
    # drop a ?lang= that would switch the language straight back
    target = re.sub(r'([?&])lang=\w+&?', r'\1', target).rstrip('?&')
    response = redirect(target or '/')
    response.set_cookie(LANG_COOKIE, code, max_age=LANG_COOKIE_AGE, samesite='Lax')
    return response


# =================================================================== homepage
FEATURES = [
    ('truck', 'feature_delivery', 'feature_delivery_sub'),
    ('lock', 'payments_secure', 'cod_or_paypal'),
    ('pen-tool', 'feature_quality', 'feature_quality_sub'),
    ('chat', 'feature_support', 'feature_support_sub'),
]


def home(request):
    HomeSection.ensure_defaults()
    products = _base_products()
    site = SiteSettings.load()
    blocks = []
    for section in HomeSection.objects.filter(is_active=True):
        limit = section.items_limit or 8
        block = {'key': section.key, 'sec': section}
        key = section.key
        if key == 'banners':
            block['items'] = list(Banner.objects.filter(is_active=True))
        elif key == 'features':
            block['items'] = [
                {'icon': icon, 'title': t(title), 'text': t(text)} for icon, title, text in FEATURES
            ]
        elif key == 'categories':
            block['items'] = list(Category.objects.filter(is_active=True, is_featured=True)[:limit])
        elif key == 'featured':
            block['items'] = list(products.filter(is_featured=True)[:limit])
        elif key == 'sale':
            block['items'] = [p for p in products[:60] if p.has_discount][:limit]
        elif key == 'new_arrivals':
            block['items'] = list(products.order_by('-created_at')[:limit])
        elif key == 'portfolio':
            works = Work.objects.filter(is_active=True).select_related('category')
            featured = list(works.filter(is_featured=True)[:limit])
            block['items'] = featured or list(works[:limit])
        elif key == 'reviews':
            # اللي مختارهم من الداشبورد «يظهر في الرئيسية» — ولو مفيش مختار، أحدث التقييمات المنشورة
            published = Review.published().select_related('user__customer')
            items = list(published.filter(is_featured=True)[:limit])
            block['items'] = items or list(published[:limit])
            block['summary'] = Review.summary()
        elif key == 'about':
            block['text'] = site.about
            block['stats'] = _story_stats('home')
            block['story'] = AboutPage.load()
            block['items'] = [1]
        else:  # hero
            block['items'] = [1]
        if block['items']:
            blocks.append(block)
    return render(request, 'pages/home.html', {'blocks': blocks})


def _story_stats(where):
    """Numbers of «حكايتنا» — the list in the dashboard, each one written or counted automatically."""
    page = AboutPage.load()
    if not (page.stats_on_home if where == 'home' else page.stats_on_page):
        return []
    return [d for d in (s.as_display() for s in AboutStat.objects.filter(is_active=True)) if d]


# ======================================================================= shop
def _filtered_products(request, category=None):
    products = _base_products()
    query = (request.GET.get('q') or '').strip()
    cat_slug = request.GET.get('category') or ''
    service_id = request.GET.get('service') or ''
    min_price = _dec(request.GET.get('min'))
    max_price = _dec(request.GET.get('max'))
    sort = request.GET.get('sort') or 'new'
    on_sale = request.GET.get('sale') == '1'

    if category is not None:
        products = products.filter(category=category)
    elif cat_slug:
        products = products.filter(category__slug=cat_slug)

    if query:
        products = products.filter(
            Q(name_ar__icontains=query) | Q(name_en__icontains=query)
            | Q(description_ar__icontains=query) | Q(description_en__icontains=query)
            | Q(sku__icontains=query)
        )
    if service_id.isdigit():
        products = products.filter(variants__service_id=int(service_id), variants__service__is_active=True)
    if min_price is not None:
        products = products.filter(price__gte=min_price)
    if max_price is not None:
        products = products.filter(price__lte=max_price)

    products = products.distinct()

    sorts = {
        'new': '-created_at',
        'price_asc': 'price',
        'price_desc': '-price',
        'name': 'name_ar',
    }
    products = products.order_by(sorts.get(sort, '-created_at'))

    result = list(products)
    if on_sale:
        result = [p for p in result if p.has_discount]
    return result, {
        'q': query,
        'category': cat_slug,
        'service': service_id,
        'min': request.GET.get('min') or '',
        'max': request.GET.get('max') or '',
        'sort': sort,
        'sale': on_sale,
    }


def _shop_services():
    """Services offered on at least one visible design (for the shop filter)."""
    return Service.objects.filter(
        is_active=True, variants__product__is_active=True,
    ).distinct().order_by('ordering', 'id')


def shop(request):
    products, active = _filtered_products(request)
    paginator = Paginator(products, PAGE_SIZE)
    page = paginator.get_page(request.GET.get('page'))
    context = {
        'page_obj': page,
        'products': page.object_list,
        'total_count': paginator.count,
        'categories': Category.objects.filter(is_active=True),
        'services': _shop_services(),
        'active': active,
        'page_title': t('shop'),
    }
    return render(request, 'pages/shop.html', context)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products, active = _filtered_products(request, category=category)
    paginator = Paginator(products, PAGE_SIZE)
    page = paginator.get_page(request.GET.get('page'))
    context = {
        'category': category,
        'page_obj': page,
        'products': page.object_list,
        'total_count': paginator.count,
        'categories': Category.objects.filter(is_active=True),
        'services': _shop_services(),
        'active': active,
        'page_title': category.name,
    }
    return render(request, 'pages/shop.html', context)


# ==================================================================== product
def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category')
        .prefetch_related('images', 'colors__images', 'variants__service', 'variants__color'),
        slug=slug, is_active=True,
    )
    Product.objects.filter(pk=product.pk).update(views=product.views + 1)

    # services have no stock: every colour × service variant is orderable,
    # and the service's extra price is added to the design's price
    variant_map = {}
    services = {}
    old_price = product.old_price
    for variant in product.variants.all():
        if variant.service_id and not variant.service.is_active:
            continue
        extra = variant.service.price if variant.service_id else Decimal('0')
        key = f'{variant.color_id or 0}-{variant.service_id or 0}'
        variant_map[key] = {
            'id': variant.id,
            'price': fmt_money(product.final_price + extra),
            'old': fmt_money(old_price + extra) if old_price else '',
        }
        if variant.service_id:
            services[variant.service_id] = variant.service

    images = list(product.images.all())
    related = (
        _base_products()
        .filter(category=product.category)
        .exclude(pk=product.pk)[:4]
    )

    context = {
        'product': product,
        'images': images,
        'colors': product.colors.all(),
        'services': sorted(services.values(), key=lambda s: (s.ordering, s.id)),
        'variant_map': variant_map,
        'related': related,
        'pd_strings': {
            'choose': t('choose_options'),
            'out': t('unavailable'),
            'in': t('available'),
        },
        'page_title': product.name,
        'og_image': product.main_image.url if product.main_image else '',
        'og_description': product.short or product.description[:200],
    }
    return render(request, 'pages/product_detail.html', context)


# ======================================================================= cart
def cart_view(request):
    cart = Cart(request)
    context = {
        'cart': cart,
        'totals': cart.totals(_saved_country(request)),
        'page_title': t('cart'),
    }
    return render(request, 'pages/cart.html', context)


@require_POST
def cart_add(request):
    variant_id = request.POST.get('variant_id')
    quantity = request.POST.get('quantity') or 1
    try:
        quantity = max(1, int(quantity))
    except (TypeError, ValueError):
        quantity = 1

    variant = (
        ProductVariant.objects.filter(id=variant_id).select_related('product', 'service').first()
        if str(variant_id or '').isdigit() else None
    )
    if not variant or not variant.is_available:
        if _is_ajax(request):
            return JsonResponse({'ok': False, 'message': t('unavailable')}, status=400)
        messages.error(request, t('unavailable'))
        return redirect(request.META.get('HTTP_REFERER', reverse('shop')))

    cart = Cart(request)
    cart.add(variant, quantity)

    if _is_ajax(request):
        return JsonResponse({
            'ok': True,
            'message': t('added_to_cart'),
            'count': cart.count,
        })
    messages.success(request, t('added_to_cart'))
    if request.POST.get('buy_now') == '1':
        return redirect('checkout')
    return redirect(request.META.get('HTTP_REFERER', reverse('cart')))


@require_POST
def cart_update(request):
    cart = Cart(request)
    for key, value in request.POST.items():
        if key.startswith('qty_'):
            variant_id = key.replace('qty_', '')
            if variant_id.isdigit():
                try:
                    cart.set_quantity(int(variant_id), int(value))
                except (TypeError, ValueError):
                    continue
    messages.success(request, t('cart_updated'))
    return redirect('cart')


def cart_remove(request, variant_id):
    cart = Cart(request)
    cart.remove(variant_id)
    messages.info(request, t('item_removed'))
    return redirect('cart')


def cart_clear(request):
    Cart(request).clear()
    messages.info(request, t('cart_cleared'))
    return redirect('cart')


@require_POST
def coupon_apply(request):
    code = (request.POST.get('code') or '').strip().upper()
    cart = Cart(request)
    coupon = Coupon.objects.filter(code=code).first()
    if not coupon:
        messages.error(request, t('coupon_invalid'))
    else:
        ok, reason = coupon.validate_for(cart.subtotal)
        if ok:
            cart.set_coupon(coupon.code)
            messages.success(request, t('coupon_applied'))
        else:
            messages.error(request, t(reason))
    return redirect(_safe_next(request, 'cart'))


def coupon_remove(request):
    Cart(request).clear_coupon()
    messages.info(request, t('coupon_removed'))
    return redirect(_safe_next(request, 'cart'))


# ================================================================== accounts
def _login_redirect(request, target):
    return redirect(f"{reverse('account_login')}?next={target}")


def _find_user(identifier):
    identifier = (identifier or '').strip()
    if not identifier:
        return None
    if '@' in identifier:
        return User.objects.filter(email__iexact=identifier).order_by('-is_active', 'id').first()
    phone = normalize_phone(identifier)
    if len(phone) < 8:
        return User.objects.filter(username__iexact=identifier).first()
    profile = CustomerProfile.objects.select_related('user').filter(phone=phone).first()
    return profile.user if profile else User.objects.filter(username__iexact=identifier).first()


def account_login(request):
    if request.user.is_authenticated:
        return redirect(_safe_next(request, 'account'))
    error = ''
    identifier = ''
    if request.method == 'POST':
        identifier = (request.POST.get('login') or '').strip()
        password = request.POST.get('password') or ''
        user = _find_user(identifier)
        auth_user = None
        if user is not None:
            auth_user = authenticate(request, username=user.get_username(), password=password)
        if auth_user is not None:
            login(request, auth_user)
            messages.success(request, t('welcome_user', name=auth_user.first_name or auth_user.get_username()))
            return redirect(_safe_next(request, 'account'))
        if user is not None and not user.is_active and user.check_password(password):
            error = t('account_disabled')
        elif user is not None and not user.has_usable_password() and _social_providers(user):
            # signed up with the Google / Discord button — there is no password to type
            error = t(_social_login_hint(user))
        else:
            error = t('login_failed')
    return render(request, 'pages/account/login.html', {
        'error': error, 'identifier': identifier,
        'next': request.GET.get('next') or request.POST.get('next') or '',
        'page_title': t('login'),
    })


def account_register(request):
    if request.user.is_authenticated:
        return redirect(_safe_next(request, 'account'))
    data = {'full_name': '', 'email': '', 'phone': ''}
    errors = {}
    if request.method == 'POST':
        for key in data:
            data[key] = (request.POST.get(key) or '').strip()
        password = request.POST.get('password') or ''
        password2 = request.POST.get('password2') or ''
        phone = normalize_phone(data['phone'])

        if not data['full_name']:
            errors['full_name'] = t('required_field')
        try:
            validate_email(data['email'])
        except ValidationError:
            errors['email'] = t('invalid_email')
        if 'email' not in errors and User.objects.filter(
            Q(email__iexact=data['email']) | Q(username__iexact=data['email'])
        ).exists():
            errors['email'] = t('email_taken')
        if not valid_phone(phone):
            errors['phone'] = t('invalid_phone')
        elif CustomerProfile.objects.filter(phone=phone).exists():
            errors['phone'] = t('phone_taken')
        if len(password) < 8:
            errors['password'] = t('password_short')
        elif password != password2:
            errors['password2'] = t('password_mismatch')

        if not errors:
            first, _, last = data['full_name'].partition(' ')
            with transaction.atomic():
                user = User.objects.create_user(
                    username=data['email'].lower()[:150], email=data['email'].lower(),
                    password=password, first_name=first[:150], last_name=last[:150],
                )
                CustomerProfile.objects.create(user=user, phone=phone)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, t('account_created'))
            return redirect(_safe_next(request, 'account'))
    return render(request, 'pages/account/register.html', {
        'data': data, 'errors': errors,
        'next': request.GET.get('next') or request.POST.get('next') or '',
        'page_title': t('register'),
    })


def account_logout(request):
    # POST only, so a prefetched link can never sign someone out
    if request.method == 'POST' and request.user.is_authenticated:
        logout(request)
        messages.info(request, t('logged_out'))
    return redirect('home')


# ------------------------------------------- sign in with Google / Discord
GOOGLE_SESSION_KEY = 'google_oauth'
DISCORD_SESSION_KEY = 'discord_oauth'

#: provider → (CustomerProfile id field, CustomerProfile picture field)
SOCIAL_FIELDS = {
    'google': ('google_id', 'google_picture'),
    'discord': ('discord_id', 'discord_avatar'),
}


def _social_providers(user):
    profile = getattr(user, 'customer', None)
    return profile.social_providers if profile else []


def _has_google(user):
    return 'google' in _social_providers(user)


def _password_hint(user):
    """«حسابي ← كلمة المرور» for an account that has no password yet."""
    providers = _social_providers(user)
    if providers == ['discord']:
        return 'set_password_hint_discord'
    if len(providers) > 1:
        return 'set_password_hint_social'
    return 'set_password_hint'


def _social_login_hint(user):
    providers = _social_providers(user)
    if providers == ['google']:
        return 'use_google_login'
    if providers == ['discord']:
        return 'use_discord_login'
    return 'use_social_login'


def _free_username(email):
    """Usernames are emails here; add a counter in the (rare) clash."""
    base = (email or '').lower()[:150] or 'customer'
    username = base
    counter = 2
    while User.objects.filter(username__iexact=username).exists():
        suffix = f'-{counter}'
        username = base[:150 - len(suffix)] + suffix
        counter += 1
    return username


def _social_account(provider, info):
    """The shopper behind a verified Google / Discord profile — found, linked or created.

    The provider has already proven the email belongs to whoever is signing in,
    so an account registered earlier with the same email is linked instead of
    duplicated; the provider's user id is stored because it survives an email
    change. (Discord emails are only used here when Discord marks them verified.)
    """
    id_field, picture_field = SOCIAL_FIELDS[provider]
    profile = CustomerProfile.objects.select_related('user').filter(**{id_field: info['sub']}).first()
    created = False

    if profile is not None:
        user = profile.user
    else:
        user = User.objects.filter(
            Q(email__iexact=info['email']) | Q(username__iexact=info['email'])
        ).order_by('-is_active', 'id').first()
        if user is None:
            created = True
            first = info['given_name'] or info['name'].partition(' ')[0]
            last = info['family_name'] or info['name'].partition(' ')[2]
            with transaction.atomic():
                # no password at all — the social button is the way in, and
                # «حسابي ← كلمة المرور» can add one later
                user = User.objects.create_user(
                    username=_free_username(info['email']), email=info['email'],
                    first_name=first[:150], last_name=last[:150],
                )
                profile = CustomerProfile.objects.create(user=user)
        else:
            profile = CustomerProfile.for_user(user)

    setattr(profile, id_field, info['sub'])
    if info['picture']:
        setattr(profile, picture_field, info['picture'])
    profile.save(update_fields=[id_field, picture_field, 'updated_at'])

    fields = []
    if not user.email and info['email'] and info.get('verified', True):
        user.email = info['email']
        fields.append('email')
    if not user.first_name and (info['given_name'] or info['name']):
        user.first_name = (info['given_name'] or info['name'].partition(' ')[0])[:150]
        fields.append('first_name')
    if fields:
        user.save(update_fields=fields)
    return user, created


def _google_account(info):
    return _social_account('google', info)


def _discord_account(info):
    return _social_account('discord', info)


def _social_signed_in(request, user, created, target):
    """Shared ending of both callbacks: log in (unless the account is switched off)."""
    if not user.is_active:
        messages.error(request, t('account_disabled'))
        return redirect('account_login')
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    if created:
        messages.success(request, t('account_created'))
    else:
        messages.success(request, t('welcome_user', name=user.first_name or user.get_username()))
    return redirect(target)


def google_login(request):
    """Step 1 — hand the customer over to Google's account chooser."""
    site = SiteSettings.load()
    target = _safe_next(request, 'account')
    if request.user.is_authenticated:
        return redirect(target)
    if not site.google_ready:
        messages.error(request, t('google_unavailable'))
        return redirect('account_login')

    state = google_oauth.random_token()
    nonce = google_oauth.random_token()
    request.session[GOOGLE_SESSION_KEY] = {'state': state, 'nonce': nonce, 'next': target}
    return redirect(google_oauth.auth_url(
        site, google_oauth.redirect_uri(request, site), state, nonce,
    ))


def google_callback(request):
    """Step 2 — Google sends the customer back with a one-time code."""
    site = SiteSettings.load()
    saved = request.session.pop(GOOGLE_SESSION_KEY, None) or {}
    target = saved.get('next') or reverse('account')
    back = f"{reverse('account_login')}?next={quote(target)}"

    if request.user.is_authenticated:
        return redirect(target)
    if not site.google_ready:
        messages.error(request, t('google_unavailable'))
        return redirect('account_login')

    if request.GET.get('error'):
        # «إلغاء» on Google's screen — not an error worth alarming anyone with
        messages.info(request, t('google_cancelled'))
        return redirect(back)

    code = request.GET.get('code') or ''
    state = request.GET.get('state') or ''
    if not code or not state or not saved.get('state') or state != saved['state']:
        messages.error(request, t('google_failed'))
        return redirect(back)

    try:
        info = google_oauth.fetch_profile(
            site, code, google_oauth.redirect_uri(request, site), saved.get('nonce', ''),
        )
    except google_oauth.GoogleError:
        messages.error(request, t('google_failed'))
        return redirect(back)

    user, created = _google_account(info)
    return _social_signed_in(request, user, created, target)


def discord_login(request):
    """Step 1 — hand the customer over to Discord's approval screen."""
    site = SiteSettings.load()
    target = _safe_next(request, 'account')
    if request.user.is_authenticated:
        return redirect(target)
    if not site.discord_ready:
        messages.error(request, t('discord_unavailable'))
        return redirect('account_login')

    state = discord_oauth.random_token()
    request.session[DISCORD_SESSION_KEY] = {'state': state, 'next': target}
    return redirect(discord_oauth.auth_url(site, discord_oauth.redirect_uri(request, site), state))


def discord_callback(request):
    """Step 2 — Discord sends the customer back with a one-time code."""
    site = SiteSettings.load()
    saved = request.session.pop(DISCORD_SESSION_KEY, None) or {}
    target = saved.get('next') or reverse('account')
    back = f"{reverse('account_login')}?next={quote(target)}"

    if request.user.is_authenticated:
        return redirect(target)
    if not site.discord_ready:
        messages.error(request, t('discord_unavailable'))
        return redirect('account_login')

    if request.GET.get('error'):
        # «Cancel» on Discord's screen
        messages.info(request, t('discord_cancelled'))
        return redirect(back)

    code = request.GET.get('code') or ''
    state = request.GET.get('state') or ''
    if not code or not state or not saved.get('state') or state != saved['state']:
        messages.error(request, t('discord_failed'))
        return redirect(back)

    try:
        info = discord_oauth.fetch_profile(site, code, discord_oauth.redirect_uri(request, site))
    except discord_oauth.DiscordError:
        messages.error(request, t('discord_failed'))
        return redirect(back)

    known = CustomerProfile.objects.filter(discord_id=info['sub']).exists()
    if not known and not (info['email'] and info['verified']):
        # a new Discord account needs a verified email to become a store account
        messages.error(request, t('discord_no_email'))
        return redirect(back)

    user, created = _discord_account(info)
    return _social_signed_in(request, user, created, target)


def _public_name(user, fallback=''):
    """«أحمد محمد» — the customer's name in two parts (first + second name)."""
    return two_part_name(user.first_name, user.last_name, fallback or user.get_username())


def account(request):
    if not request.user.is_authenticated:
        return _login_redirect(request, reverse('account'))
    user = request.user
    profile = CustomerProfile.for_user(user)
    tab = request.GET.get('tab') or 'orders'
    if user.is_staff and tab == 'orders':  # the store's staff see customers' orders in the dashboard
        tab = 'profile'
    errors = {}

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'profile':
            tab = 'profile'
            full_name = (request.POST.get('full_name') or '').strip()
            email = (request.POST.get('email') or '').strip()
            phone = normalize_phone(request.POST.get('phone'))
            if not full_name:
                errors['full_name'] = t('required_field')
            try:
                validate_email(email)
            except ValidationError:
                errors['email'] = t('invalid_email')
            if 'email' not in errors and User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                errors['email'] = t('email_taken')
            if not valid_phone(phone):
                errors['phone'] = t('invalid_phone')
            elif CustomerProfile.objects.filter(phone=phone).exclude(pk=profile.pk).exists():
                errors['phone'] = t('phone_taken')
            if not errors:
                first, _, last = full_name.partition(' ')
                user.first_name, user.last_name = first[:150], last[:150]
                user.email = email.lower()
                user.save(update_fields=['first_name', 'last_name', 'email'])
                country_id = request.POST.get('country') or ''
                profile.phone = phone
                profile.phone_alt = normalize_phone(request.POST.get('phone_alt'))
                profile.country = Country.objects.filter(pk=country_id).first() if country_id.isdigit() else None
                profile.city = (request.POST.get('city') or '').strip()[:120]
                profile.address = (request.POST.get('address') or '').strip()
                profile.save()
                messages.success(request, t('profile_saved'))
                return redirect(f"{reverse('account')}?tab=profile")
        elif action in ('avatar', 'avatar_remove'):
            tab = 'profile'
            if action == 'avatar_remove':
                if profile.avatar:
                    profile.avatar.delete(save=False)
                profile.avatar = None
                profile.save(update_fields=['avatar', 'updated_at'])
                messages.success(request, t('photo_removed'))
                return redirect(f"{reverse('account')}?tab=profile")
            upload = request.FILES.get('avatar')
            error = _avatar_error(upload)
            if error:
                errors['avatar'] = error
            else:
                old = profile.avatar.name if profile.avatar else ''
                profile.avatar.save(f'{user.pk}.jpg', _square_avatar(upload), save=False)
                profile.save(update_fields=['avatar', 'updated_at'])
                if old and old != profile.avatar.name:
                    profile.avatar.storage.delete(old)
                messages.success(request, t('photo_saved'))
                return redirect(f"{reverse('account')}?tab=profile")
        elif action == 'password':
            tab = 'password'
            current = request.POST.get('current_password') or ''
            new = request.POST.get('new_password') or ''
            # a Google account has no password yet, so there is none to confirm
            if user.has_usable_password() and not user.check_password(current):
                errors['current_password'] = t('wrong_password')
            elif len(new) < 8:
                errors['new_password'] = t('password_short')
            else:
                user.set_password(new)
                user.save(update_fields=['password'])
                update_session_auth_hash(request, user)
                messages.success(request, t('password_changed'))
                return redirect(f"{reverse('account')}?tab=password")

    orders = user.orders.prefetch_related('items').select_related('review')
    return render(request, 'pages/account/account.html', {
        'profile': profile,
        'orders': orders,
        'tab': tab,
        'errors': errors,
        'has_password': user.has_usable_password(),
        'password_hint': _password_hint(user),
        'countries': shipping_countries(include=profile.country),
        'can_review': reviewable_orders(user).exists(),
        'page_title': t('account'),
    })


AVATAR_MAX_MB = 5
AVATAR_SIZE = 400  # px — saved square, center-cropped


def _avatar_error(upload):
    if not upload:
        return t('required_field')
    if upload.size > AVATAR_MAX_MB * 1024 * 1024:
        return t('photo_too_big')
    try:
        from PIL import Image
        with Image.open(upload) as img:
            img.verify()
        upload.seek(0)
    except Exception:
        return t('photo_invalid')
    return ''


def _square_avatar(upload):
    """Center-crop to a square and shrink to AVATAR_SIZE — small, fast, same shape everywhere."""
    from io import BytesIO
    from django.core.files.base import ContentFile
    from PIL import Image, ImageOps
    with Image.open(upload) as img:
        img = ImageOps.exif_transpose(img).convert('RGB')
        img = ImageOps.fit(img, (AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)
        out = BytesIO()
        img.save(out, format='JPEG', quality=86, optimize=True)
    return ContentFile(out.getvalue())


def _owned_order_or_404(request, number):
    order = get_object_or_404(
        Order.objects.prefetch_related('items').select_related('country', 'user'),
        order_number=number,
    )
    user = request.user
    if user.is_authenticated and (user.is_staff or order.user_id == user.id):
        return order
    if order.user_id is None and request.session.get('last_order') == order.order_number:
        return order
    raise Http404


def account_order(request, number):
    if not request.user.is_authenticated:
        return _login_redirect(request, reverse('account_order', args=[number]))
    order = _owned_order_or_404(request, number)
    return render(request, 'pages/account/order.html', {
        'order': order,
        'can_review': order.is_paid and not hasattr(order, 'review') and order.user_id == request.user.id,
        'page_title': f"{t('order_number')} {order.order_number}",
    })


# =================================================================== checkout
def _checkout_defaults(user, profile):
    return {
        'full_name': user.get_full_name() or user.first_name,
        'phone': profile.phone,
        'phone_alt': profile.phone_alt,
        'email': user.email,
        'country': str(profile.country_id or ''),
        'city': profile.city,
        'address': profile.address,
        'notes': '',
    }


def checkout(request):
    cart = Cart(request)
    site = SiteSettings.load()
    countries = shipping_countries()

    if cart.is_empty:
        messages.info(request, t('checkout_empty'))
        return redirect('cart')

    if not site.orders_enabled:
        messages.error(request, t('orders_disabled'))
        return redirect('cart')

    if not request.user.is_authenticated:
        messages.info(request, t('login_required_checkout'))
        return _login_redirect(request, reverse('checkout'))

    methods = site.payment_methods
    if not methods:
        messages.error(request, t('no_payment_methods'))
        return redirect('cart')

    user = request.user
    profile = CustomerProfile.for_user(user)
    errors = {}
    data = _checkout_defaults(user, profile)
    data['payment_method'] = methods[0]
    if len(countries) == 1 and not data['country']:
        data['country'] = str(countries[0].pk)

    if request.method == 'POST':
        for key in data:
            data[key] = (request.POST.get(key) or '').strip()
        if data['payment_method'] not in methods:
            data['payment_method'] = methods[0]

        phone = normalize_phone(data['phone'])
        if not data['full_name']:
            errors['full_name'] = t('required_field')
        if not valid_phone(phone):
            errors['phone'] = t('invalid_phone')
        if not data['address']:
            errors['address'] = t('required_field')
        if data['email']:
            try:
                validate_email(data['email'])
            except ValidationError:
                errors['email'] = t('invalid_email')

        country = next((c for c in countries if str(c.pk) == data['country']), None)
        if countries and country is None:
            errors['country'] = t('choose_country')

        if not errors:
            method = data['payment_method']
            totals = cart.totals(country, method)
            with transaction.atomic():
                order = Order.objects.create(
                    user=user,
                    full_name=data['full_name'],
                    phone=phone,
                    phone_alt=normalize_phone(data['phone_alt']),
                    email=data['email'] or user.email,
                    country=country,
                    city=data['city'],
                    address=data['address'],
                    notes=data['notes'],
                    subtotal=totals['subtotal'],
                    discount_total=totals['discount'],
                    coupon=totals['coupon'],
                    coupon_code=totals['coupon'].code if totals['coupon'] else '',
                    shipping_fee=totals['shipping'],
                    fees_total=totals['fees'],
                    total=totals['total'],
                    payment_method=method,
                    payment_status='unpaid',
                    pay_amount=site.to_paypal_amount(totals['total']) if method == 'paypal' else None,
                    pay_currency=(site.paypal_currency or 'USD') if method == 'paypal' else '',
                )
                for row in cart.rows:
                    variant = row['variant']
                    OrderItem.objects.create(
                        order=order,
                        product=row['product'],
                        variant=variant,
                        product_name=row['product'].name,
                        color_name=row['color'].name if row['color'] else '',
                        service_name=row['service'].name if row['service'] else '',
                        image_url=row['image'].url if row['image'] else '',
                        unit_price=row['unit_price'],
                        quantity=row['quantity'],
                        line_total=row['line_total'],
                    )
                if totals['coupon']:
                    Coupon.objects.filter(pk=totals['coupon'].pk).update(
                        used_count=totals['coupon'].used_count + 1
                    )

                # the customer's details land in «العملاء» in the dashboard
                profile.phone = profile.phone or phone
                if not CustomerProfile.objects.filter(phone=phone).exclude(pk=profile.pk).exists():
                    profile.phone = phone
                profile.phone_alt = normalize_phone(data['phone_alt']) or profile.phone_alt
                profile.country = country or profile.country
                profile.city = data['city'] or profile.city
                profile.address = data['address']
                profile.save()
                if not (user.first_name or user.last_name):
                    first, _, last = data['full_name'].partition(' ')
                    user.first_name, user.last_name = first[:150], last[:150]
                    user.save(update_fields=['first_name', 'last_name'])

            cart.clear()
            mailer.order_placed(order)
            request.session['last_order'] = order.order_number
            if method == 'paypal':
                return redirect('order_pay', number=order.order_number)
            return redirect('order_success', number=order.order_number)

    selected = next((c for c in countries if str(c.pk) == data['country']), None)
    context = {
        'cart': cart,
        'totals': cart.totals(selected, data['payment_method']),
        'countries': countries,
        'ship_options': cart.shipping_options(countries),
        'data': data,
        'errors': errors,
        'methods': methods,
        'page_title': t('checkout_title'),
    }
    return render(request, 'pages/checkout.html', context)


def _paypal_link_for(site, order):
    link = (site.paypal_link or '').strip()
    if not link:
        return ''
    host = urlparse(link).netloc.lower()
    if host.endswith('paypal.me') and order.pay_amount:
        return f"{link.rstrip('/')}/{order.pay_amount}{order.pay_currency or 'USD'}"
    return link


def order_pay(request, number):
    if not request.user.is_authenticated:
        return _login_redirect(request, reverse('order_pay', args=[number]))
    order = _owned_order_or_404(request, number)
    site = SiteSettings.load()
    if order.is_paid or order.payment_method != 'paypal' or order.status == 'cancelled':
        return redirect('order_success', number=order.order_number)
    if not order.pay_amount:
        order.pay_amount = site.to_paypal_amount(order.total)
        order.pay_currency = site.paypal_currency or 'USD'
        order.save(update_fields=['pay_amount', 'pay_currency', 'updated_at'])
    return render(request, 'pages/payment.html', {
        'order': order,
        'smart': site.paypal_smart_ready,
        'client_id': site.paypal_client_id,
        'pay_link': _paypal_link_for(site, order),
        'rate': money(site.paypal_rate),
        'page_title': t('payment_title'),
    })


@require_POST
def paypal_create(request, number):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False}, status=403)
    order = _owned_order_or_404(request, number)
    site = SiteSettings.load()
    if order.is_paid:
        return JsonResponse({'ok': False, 'message': t('already_paid')}, status=400)
    if not site.paypal_smart_ready:
        return JsonResponse({'ok': False, 'message': t('payment_error')}, status=400)
    try:
        paypal_id, _ = paypal.create_order(site, order, site.brand_name)
    except paypal.PayPalError:
        return JsonResponse({'ok': False, 'message': t('payment_error')}, status=502)
    order.paypal_order_id = paypal_id
    order.save(update_fields=['paypal_order_id', 'updated_at'])
    return JsonResponse({'ok': True, 'id': paypal_id})


@require_POST
def paypal_capture(request, number):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False}, status=403)
    order = _owned_order_or_404(request, number)
    site = SiteSettings.load()
    success_url = reverse('order_success', args=[order.order_number])
    if order.is_paid:
        return JsonResponse({'ok': True, 'redirect': success_url})

    paypal_id = request.POST.get('orderID') or ''
    if not paypal_id or paypal_id != order.paypal_order_id:
        return JsonResponse({'ok': False, 'message': t('payment_failed')}, status=400)
    try:
        data = paypal.capture_order(site, paypal_id)
    except paypal.PayPalError:
        return JsonResponse({'ok': False, 'message': t('payment_error')}, status=502)

    result = paypal.completed_capture(data)
    expected = (order.pay_amount or Decimal('0')).quantize(Decimal('0.01'))
    if not result or result[1].quantize(Decimal('0.01')) != expected \
            or result[2].upper() != (order.pay_currency or 'USD').upper():
        order.payment_status = 'failed'
        order.save(update_fields=['payment_status', 'updated_at'])
        return JsonResponse({'ok': False, 'message': t('payment_failed')}, status=400)

    order.paypal_capture_id, _, _, order.payer_email = result
    order.save(update_fields=['paypal_capture_id', 'payer_email', 'updated_at'])
    order.mark_paid()
    messages.success(request, t('payment_success'))
    return JsonResponse({'ok': True, 'redirect': success_url})


@require_POST
def order_paid_manual(request, number):
    if not request.user.is_authenticated:
        return _login_redirect(request, reverse('order_pay', args=[number]))
    order = _owned_order_or_404(request, number)
    if order.is_paid:
        return redirect('order_success', number=order.order_number)
    order.payment_status = 'pending'
    order.payment_reference = (request.POST.get('reference') or '').strip()[:120]
    order.save(update_fields=['payment_status', 'payment_reference', 'updated_at'])
    messages.success(request, t('payment_submitted'))
    return redirect('order_success', number=order.order_number)


def order_success(request, number):
    order = _owned_order_or_404(request, number)
    return render(request, 'pages/order_success.html', {
        'order': order,
        'can_review': (
            order.is_paid and request.user.is_authenticated
            and order.user_id == request.user.id and not hasattr(order, 'review')
        ),
        'page_title': t('order_received'),
    })


def track_order(request):
    order = None
    not_found = False
    number = (request.GET.get('number') or '').strip().upper()
    phone = normalize_phone(request.GET.get('phone'))
    if number and phone:
        order = (
            Order.objects.prefetch_related('items')
            .select_related('country')
            .filter(order_number=number, phone__endswith=phone[-8:])
            .first()
        )
        not_found = order is None
    return render(request, 'pages/track_order.html', {
        'order': order,
        'not_found': not_found,
        'number': number,
        'phone': request.GET.get('phone') or '',
        'page_title': t('track_title'),
    })


# ================================================================= portfolio
def works(request):
    items = Work.objects.filter(is_active=True).select_related('category').annotate(
        n_media=Count('media')
    ).order_by('ordering', '-created_at')
    cat = request.GET.get('cat') or ''
    categories = WorkCategory.objects.filter(works__is_active=True).distinct()
    if cat:
        items = items.filter(category__slug=cat)
    page = Paginator(items, PAGE_SIZE).get_page(request.GET.get('page'))
    return render(request, 'pages/works.html', {
        'page_obj': page,
        'works': page.object_list,
        'categories': categories,
        'active_cat': cat,
        'page_title': t('portfolio'),
        'og_description': t('portfolio_sub'),
    })


def work_detail(request, slug):
    work = get_object_or_404(
        Work.objects.select_related('category').prefetch_related('media'), slug=slug, is_active=True
    )
    Work.objects.filter(pk=work.pk).update(views=work.views + 1)
    siblings = list(Work.objects.filter(is_active=True).values_list('pk', flat=True))
    prev_work = next_work = None
    if work.pk in siblings:
        i = siblings.index(work.pk)
        if i > 0:
            prev_work = Work.objects.get(pk=siblings[i - 1])
        if i < len(siblings) - 1:
            next_work = Work.objects.get(pk=siblings[i + 1])
    related = Work.objects.filter(is_active=True).exclude(pk=work.pk)
    if work.category_id:
        related = related.filter(category_id=work.category_id)
    media = list(work.media.all())
    return render(request, 'pages/work_detail.html', {
        'work': work,
        'media': media,
        'photos': sum(1 for m in media if m.kind == 'image'),
        'videos': sum(1 for m in media if m.is_video),
        'prev_work': prev_work,
        'next_work': next_work,
        'related': related[:3],
        'page_title': work.title,
        'og_type': 'article',
        'og_image': work.cover.url if work.cover else '',
        'og_description': work.share_text,
        'share_url': request.build_absolute_uri(work.get_absolute_url()),
    })


# =================================================================== reviews
def reviews(request):
    site = SiteSettings.load()
    published = Review.published().select_related('order')
    page = Paginator(published, PAGE_SIZE).get_page(request.GET.get('page'))
    user = request.user
    state = 'login'
    if user.is_authenticated:
        if reviewable_orders(user).exists():
            state = 'can'
        elif Order.objects.filter(user=user, payment_status='paid').exists():
            state = 'done'
        else:
            state = 'need_order'
    my_pending = []
    if user.is_authenticated:
        my_pending = list(Review.objects.filter(user=user, is_approved=False)[:3])
    return render(request, 'pages/reviews.html', {
        'page_obj': page,
        'reviews': page.object_list,
        'summary': Review.summary(),
        'state': state,
        'order_choices': list(reviewable_orders(user)[:10]) if state == 'can' else [],
        'my_pending': my_pending,
        'auto_publish': site.reviews_auto_publish,
        'page_title': t('reviews'),
        'og_description': t('reviews_sub'),
    })


@require_POST
def review_submit(request):
    if not request.user.is_authenticated:
        return _login_redirect(request, reverse('reviews'))
    user = request.user
    eligible = reviewable_orders(user)
    order_id = request.POST.get('order') or ''
    order = eligible.filter(pk=order_id).first() if order_id.isdigit() else eligible.first()
    if order is None:
        messages.error(request, t('review_need_order'))
        return redirect('reviews')
    try:
        rating = int(request.POST.get('rating') or 0)
    except ValueError:
        rating = 0
    comment = (request.POST.get('comment') or '').strip()
    if rating not in range(1, 6):
        messages.error(request, t('review_choose_rating'))
        return redirect(f"{reverse('reviews')}#write")
    if len(comment) < 5:
        messages.error(request, t('review_write_more'))
        return redirect(f"{reverse('reviews')}#write")
    site = SiteSettings.load()
    review = Review.objects.create(
        user=user, order=order,
        name=_public_name(user, order.full_name)[:120],
        rating=rating, comment=comment[:2000],
        is_approved=site.reviews_auto_publish,
    )
    mailer.review_added(review)
    note = t('review_thanks') if site.reviews_auto_publish else f"{t('review_thanks')} — {t('review_pending')}"
    messages.success(request, note)
    return redirect('reviews')


# =================================================================== support
def _attachment_warning(request, rejected):
    if rejected:
        messages.warning(request, t('files_rejected', names='، '.join(rejected[:3]),
                                    size=TICKET_MAX_FILE_MB))


def is_support_staff(user):
    """The store side of support: staff with the «الرسائل وتذاكر الدعم» permission."""
    return bool(user and user.is_authenticated and 'messages' in staff_permissions(user))


@login_required
def support_list(request):
    """«الدعم» — the customer sees their own tickets, the store sees every ticket."""
    staff = is_support_staff(request.user)
    tickets = Ticket.objects.select_related('order', 'user').annotate(replies=Count('messages'))
    status = request.GET.get('status') or ''
    if staff:
        if status in dict(TICKET_STATUSES):
            tickets = tickets.filter(status=status)
        tickets = tickets.order_by('-admin_unread', '-last_message_at')
        counts = {
            'all': Ticket.objects.count(),
            'open': Ticket.objects.filter(status='open').count(),
            'answered': Ticket.objects.filter(status='answered').count(),
            'closed': Ticket.objects.filter(status='closed').count(),
        }
    else:
        tickets = tickets.filter(user=request.user)
        counts = {}
    return render(request, 'pages/account/tickets.html', {
        'tickets': tickets[:100] if staff else tickets,
        'support_staff': staff, 'status': status, 'counts': counts,
        'page_title': t('customer_tickets') if staff else t('support'),
    })


@login_required
def support_new(request):
    if is_support_staff(request.user):
        messages.info(request, t('staff_no_new_ticket'))
        return redirect('support')
    recent_orders = request.user.orders.order_by('-created_at')
    orders = list(recent_orders[:20])
    data = {'subject': '', 'topic': 'other', 'order': '', 'body': ''}
    errors = {}
    if request.method == 'POST':
        for key in data:
            data[key] = (request.POST.get(key) or '').strip()
        files = ticket_uploads(request)
        if not data['subject']:
            errors['subject'] = t('required_field')
        if not data['body'] and not files:
            errors['body'] = t('required_field')
        if data['topic'] not in dict(TICKET_TOPICS):
            data['topic'] = 'other'
        order = next((o for o in orders if str(o.pk) == data['order']), None)

        if not errors:
            with transaction.atomic():
                ticket = Ticket.objects.create(
                    user=request.user, subject=data['subject'][:160],
                    topic=data['topic'], order=order,
                )
                message = TicketMessage.objects.create(
                    ticket=ticket, author=request.user, is_staff=False, body=data['body'][:4000],
                )
                rejected = save_ticket_attachments(message, files)
            _attachment_warning(request, rejected)
            mailer.ticket_opened(ticket, message)
            messages.success(request, t('ticket_created', number=ticket.number))
            return redirect('support_detail', number=ticket.number)

    return render(request, 'pages/account/ticket_new.html', {
        'data': data, 'errors': errors, 'orders': orders,
        'topics': [(key, pick(*label)) for key, label in _topic_labels()],
        'max_files': TICKET_MAX_FILES, 'max_mb': TICKET_MAX_FILE_MB,
        'page_title': t('new_ticket'),
    })


def _topic_labels():
    from .models import TICKET_TOPIC_LABELS
    return [(key, TICKET_TOPIC_LABELS[key]) for key, _ in TICKET_TOPICS]


@login_required
def support_detail(request, number):
    """One conversation. The customer sees their own; the store opens any of them
    and answers without going into the dashboard."""
    staff = is_support_staff(request.user)
    base = Ticket.objects.select_related('order', 'user')
    ticket = get_object_or_404(base, number=number) if staff else get_object_or_404(
        base, number=number, user=request.user
    )

    if request.method == 'POST':
        if staff and request.POST.get('action') == 'status':
            new_status = request.POST.get('status') or ''
            if new_status in dict(TICKET_STATUSES):
                ticket.status = new_status
                ticket.save(update_fields=['status', 'updated_at'])
                messages.success(request, f"{t('ticket_status')}: {ticket.status_label}")
            return redirect('support_detail', number=ticket.number)

        if ticket.is_closed:
            messages.info(request, t('ticket_closed_note'))
            return redirect('support_detail', number=ticket.number)
        body = (request.POST.get('body') or '').strip()
        files = ticket_uploads(request)
        if not body and not files:
            messages.error(request, t('required_field'))
            return redirect('support_detail', number=ticket.number)
        with transaction.atomic():
            message = TicketMessage.objects.create(
                ticket=ticket, author=request.user, is_staff=staff, body=body[:4000],
            )
            rejected = save_ticket_attachments(message, files)
            ticket.touch(from_staff=staff)
        _attachment_warning(request, rejected)
        if staff:
            mailer.ticket_staff_replied(ticket, message)
        else:
            mailer.ticket_customer_replied(ticket, message)
        messages.success(request, t('reply_sent'))
        return redirect('support_detail', number=ticket.number)

    if staff:
        if ticket.admin_unread:
            Ticket.objects.filter(pk=ticket.pk).update(admin_unread=False)
            ticket.admin_unread = False
    elif ticket.user_unread:
        Ticket.objects.filter(pk=ticket.pk).update(user_unread=False)
    return render(request, 'pages/account/ticket_detail.html', {
        'ticket': ticket,
        'ticket_messages': ticket.messages.prefetch_related('attachments').select_related('author'),
        'max_files': TICKET_MAX_FILES, 'max_mb': TICKET_MAX_FILE_MB,
        'support_staff': staff, 'statuses': TICKET_STATUSES,
        'page_title': f'{t("ticket")} {ticket.number}',
    })


# ===================================================================== pages
def about(request):
    HomeSection.ensure_defaults()
    section = HomeSection.objects.filter(key='about').first()
    page = AboutPage.load()
    return render(request, 'pages/about.html', {
        'sec': section,
        'story': page,
        'stats': _story_stats('page'),
        'page_title': page.page_title or t('about'),
        'og_description': page.page_subtitle or '',
    })


def policy_detail(request, slug):
    policy = get_object_or_404(Policy, slug=slug, is_active=True)
    return render(request, 'pages/policy.html', {
        'policy': policy,
        'others': Policy.objects.filter(is_active=True).exclude(pk=policy.pk),
        'page_title': policy.title,
    })


def contact(request):
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        message = (request.POST.get('message') or '').strip()
        if name and message:
            contact_message = ContactMessage.objects.create(
                name=name,
                email=(request.POST.get('email') or '').strip(),
                phone=(request.POST.get('phone') or '').strip(),
                subject=(request.POST.get('subject') or '').strip(),
                message=message,
            )
            mailer.contact_message(contact_message)
            messages.success(request, t('message_sent'))
            return redirect('contact')
        messages.error(request, t('required_field'))
    return render(request, 'pages/contact.html', {'page_title': t('contact_title')})


# ===================================================================== errors
def error_404(request, exception=None):
    return render(request, 'pages/404.html', status=404)


def error_500(request):
    return render(request, 'pages/500.html', status=500)
