"""Storefront views — RGS TOWER."""

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .i18n import t
from .models import (
    Banner, Category, ContactMessage, Coupon, Governorate, Order, OrderItem,
    Product, ProductVariant, SiteSettings, Size,
)
from .utils import Cart, money

PAGE_SIZE = 12


def _dec(value, default=None):
    try:
        return Decimal(str(value))
    except (TypeError, ValueError, InvalidOperation):
        return default


def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _base_products():
    return (
        Product.objects.filter(is_active=True)
        .select_related('category')
        .prefetch_related('images', 'colors', 'variants')
    )


# =================================================================== homepage
def home(request):
    products = _base_products()
    context = {
        'banners': Banner.objects.filter(is_active=True),
        'categories': Category.objects.filter(is_active=True, is_featured=True)[:6],
        'featured': products.filter(is_featured=True)[:8],
        'new_arrivals': products.order_by('-created_at')[:8],
        'sale_products': [p for p in products[:40] if p.has_discount][:8],
    }
    return render(request, 'pages/home.html', context)


# ======================================================================= shop
def _filtered_products(request, category=None):
    products = _base_products()
    query = (request.GET.get('q') or '').strip()
    cat_slug = request.GET.get('category') or ''
    size_id = request.GET.get('size') or ''
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
    if size_id.isdigit():
        products = products.filter(variants__size_id=int(size_id), variants__quantity__gt=0)
    if min_price is not None:
        products = products.filter(price__gte=min_price)
    if max_price is not None:
        products = products.filter(price__lte=max_price)

    products = products.distinct()

    sorts = {
        'new': '-created_at',
        'price_asc': 'price',
        'price_desc': '-price',
        'name': 'name_en',
    }
    products = products.order_by(sorts.get(sort, '-created_at'))

    result = list(products)
    if on_sale:
        result = [p for p in result if p.has_discount]
    return result, {
        'q': query,
        'category': cat_slug,
        'size': size_id,
        'min': request.GET.get('min') or '',
        'max': request.GET.get('max') or '',
        'sort': sort,
        'sale': on_sale,
    }


def shop(request):
    products, active = _filtered_products(request)
    paginator = Paginator(products, PAGE_SIZE)
    page = paginator.get_page(request.GET.get('page'))
    context = {
        'page_obj': page,
        'products': page.object_list,
        'total_count': paginator.count,
        'categories': Category.objects.filter(is_active=True),
        'sizes': Size.objects.all(),
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
        'sizes': Size.objects.all(),
        'active': active,
        'page_title': category.name,
    }
    return render(request, 'pages/shop.html', context)


# ==================================================================== product
def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category')
        .prefetch_related('images', 'colors__images', 'variants__size', 'variants__color'),
        slug=slug, is_active=True,
    )
    Product.objects.filter(pk=product.pk).update(views=product.views + 1)

    variant_map = {}
    for variant in product.variants.all():
        key = f'{variant.color_id or 0}-{variant.size_id or 0}'
        variant_map[key] = {'id': variant.id, 'qty': variant.quantity}

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
        'sizes': Size.objects.filter(variants__product=product).distinct(),
        'variant_map': variant_map,
        'related': related,
        'pd_strings': {
            'choose': t('choose_options'),
            'out': t('out_of_stock'),
            'in': t('in_stock'),
            'only': t('only_left'),
            'left': t('pieces_left'),
        },
        'page_title': product.name,
    }
    return render(request, 'pages/product_detail.html', context)


# ======================================================================= cart
def cart_view(request):
    cart = Cart(request)
    context = {
        'cart': cart,
        'totals': cart.totals(),
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

    variant = ProductVariant.objects.filter(id=variant_id).select_related('product').first()
    if not variant or not variant.product.is_active or variant.quantity <= 0:
        if _is_ajax(request):
            return JsonResponse({'ok': False, 'message': t('out_of_stock')}, status=400)
        messages.error(request, t('out_of_stock'))
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
    return redirect(request.POST.get('next') or 'cart')


def coupon_remove(request):
    Cart(request).clear_coupon()
    messages.info(request, t('coupon_removed'))
    return redirect(request.GET.get('next') or 'cart')


# =================================================================== checkout
def checkout(request):
    cart = Cart(request)
    site = SiteSettings.load()
    governorates = Governorate.objects.filter(is_active=True)

    if cart.is_empty:
        messages.info(request, t('checkout_empty'))
        return redirect('cart')

    if not site.orders_enabled:
        messages.error(request, t('orders_disabled'))
        return redirect('cart')

    errors = {}
    data = {
        'full_name': '', 'phone': '', 'phone_alt': '', 'email': '',
        'governorate': '', 'city': '', 'address': '', 'notes': '',
    }

    if request.method == 'POST':
        for key in data:
            data[key] = (request.POST.get(key) or '').strip()

        if not data['full_name']:
            errors['full_name'] = t('required_field')
        if not data['phone'] or len(data['phone']) < 8:
            errors['phone'] = t('required_field')
        if not data['address']:
            errors['address'] = t('required_field')

        governorate = None
        if data['governorate'].isdigit():
            governorate = governorates.filter(id=int(data['governorate'])).first()
        if governorates.exists() and governorate is None:
            errors['governorate'] = t('required_field')

        if not errors:
            totals = cart.totals(governorate)
            with transaction.atomic():
                order = Order.objects.create(
                    full_name=data['full_name'],
                    phone=data['phone'],
                    phone_alt=data['phone_alt'],
                    email=data['email'],
                    governorate=governorate,
                    city=data['city'],
                    address=data['address'],
                    notes=data['notes'],
                    subtotal=totals['subtotal'],
                    discount_total=totals['discount'],
                    coupon=totals['coupon'],
                    coupon_code=totals['coupon'].code if totals['coupon'] else '',
                    shipping_fee=totals['shipping'],
                    total=totals['total'],
                )
                for row in cart.rows:
                    variant = row['variant']
                    OrderItem.objects.create(
                        order=order,
                        product=row['product'],
                        variant=variant,
                        product_name=row['product'].name,
                        color_name=row['color'].name if row['color'] else '',
                        size_name=row['size'].label if row['size'] else '',
                        image_url=row['image'].url if row['image'] else '',
                        unit_price=row['unit_price'],
                        quantity=row['quantity'],
                        line_total=row['line_total'],
                    )
                    ProductVariant.objects.filter(pk=variant.pk).update(
                        quantity=max(0, variant.quantity - row['quantity'])
                    )
                if totals['coupon']:
                    Coupon.objects.filter(pk=totals['coupon'].pk).update(
                        used_count=totals['coupon'].used_count + 1
                    )
            cart.clear()
            request.session['last_order'] = order.order_number
            return redirect('order_success', number=order.order_number)

    context = {
        'cart': cart,
        'totals': cart.totals(),
        'governorates': governorates,
        'data': data,
        'errors': errors,
        'page_title': t('checkout_title'),
    }
    return render(request, 'pages/checkout.html', context)


def order_success(request, number):
    order = get_object_or_404(
        Order.objects.prefetch_related('items').select_related('governorate'),
        order_number=number,
    )
    return render(request, 'pages/order_success.html', {
        'order': order,
        'page_title': t('order_received'),
    })


def track_order(request):
    order = None
    not_found = False
    number = (request.GET.get('number') or '').strip().upper()
    phone = (request.GET.get('phone') or '').strip()
    if number and phone:
        order = (
            Order.objects.prefetch_related('items')
            .select_related('governorate')
            .filter(order_number=number, phone__endswith=phone[-8:])
            .first()
        )
        not_found = order is None
    return render(request, 'pages/track_order.html', {
        'order': order,
        'not_found': not_found,
        'number': number,
        'phone': phone,
        'page_title': t('track_title'),
    })


# ===================================================================== static
def about(request):
    return render(request, 'pages/about.html', {'page_title': t('about')})


def contact(request):
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        message = (request.POST.get('message') or '').strip()
        if name and message:
            ContactMessage.objects.create(
                name=name,
                email=(request.POST.get('email') or '').strip(),
                phone=(request.POST.get('phone') or '').strip(),
                subject=(request.POST.get('subject') or '').strip(),
                message=message,
            )
            messages.success(request, t('message_sent'))
            return redirect('contact')
        messages.error(request, t('required_field'))
    return render(request, 'pages/contact.html', {'page_title': t('contact_title')})


# ===================================================================== errors
def error_404(request, exception=None):
    return render(request, 'pages/404.html', status=404)


def error_500(request):
    return render(request, 'pages/500.html', status=500)
