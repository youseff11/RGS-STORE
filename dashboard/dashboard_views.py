"""Admin dashboard views — RGS TOWER."""

import csv
from datetime import timedelta
from decimal import Decimal
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, F, Max, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    AnnouncementForm, BannerForm, CategoryForm, ColorForm, CouponForm,
    CountryForm, GoogleLoginForm, HomeSectionForm, NavLinkForm, NotificationSettingsForm,
    PaymentSettingsForm, PolicyForm, ProductForm, PromotionForm, ReviewForm, SiteSettingsForm,
    ServiceForm, StaffForm, WorkCategoryForm, WorkForm,
)
from . import google_oauth, mailer
from .models import (
    Announcement, Banner, Category, ContactMessage, Country, Coupon, CustomerProfile,
    HomeSection, NavLink, Order, OrderItem, Policy, Product, ProductColor, ProductImage,
    PAYMENT_STATUSES, Promotion, Review, STAFF_PERMISSIONS, Service, SiteSettings, StaffProfile,
    TICKET_MAX_FILES, TICKET_MAX_FILE_MB, TICKET_STATUSES, Ticket, TicketMessage, Work,
    WorkCategory, WorkMedia, ensure_policy_defaults, staff_permissions,
)

from .utils import save_ticket_attachments, ticket_uploads

User = get_user_model()

staff_required = user_passes_test(
    lambda u: u.is_authenticated and u.is_active and u.is_staff,
    login_url='/dashboard/login/',
)


def perm_required(perm):
    """Staff only + the dashboard section `perm` must be in the user's permissions."""
    def decorator(view):
        @staff_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if perm not in staff_permissions(request.user):
                messages.error(request, 'مش عندك صلاحية تفتح القسم ده')
                return redirect('dash_index')
            return view(request, *args, **kwargs)
        return wrapper
    return decorator

PAGE_SIZE = 20


def _paginate(request, queryset, size=PAGE_SIZE):
    return Paginator(queryset, size).get_page(request.GET.get('page'))


def _pending_counts():
    return {
        'new_orders': Order.objects.filter(status='pending').count(),
        'unread_messages': ContactMessage.objects.filter(is_read=False).count(),
        'new_tickets': Ticket.objects.filter(admin_unread=True).exclude(status='closed').count(),
        'open_tickets': Ticket.objects.exclude(status='closed').count(),
        'pending_reviews': Review.objects.filter(is_approved=False).count(),
        'pending_payments': Order.objects.filter(payment_status='pending').exclude(status='cancelled').count(),
    }


# ======================================================================= auth
def login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dash_index')
    error = ''
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            return redirect(request.GET.get('next') or 'dash_index')
        error = 'بيانات الدخول غير صحيحة / Invalid credentials'
    return render(request, 'dashboard/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('dash_login')


# ================================================================== overview
@staff_required
def index(request):
    now = timezone.now()
    month_ago = now - timedelta(days=30)
    week_ago = now - timedelta(days=7)

    orders = Order.objects.all()
    paid_statuses = ['confirmed', 'shipped', 'delivered']
    revenue = orders.filter(status__in=paid_statuses).aggregate(t=Sum('total'))['t'] or Decimal('0')
    month_revenue = orders.filter(
        status__in=paid_statuses, created_at__gte=month_ago
    ).aggregate(t=Sum('total'))['t'] or Decimal('0')

    # services customers order the most (by the name saved on each order line)
    top_services = (
        OrderItem.objects.exclude(service_name='').exclude(order__status='cancelled')
        .values('service_name').annotate(count=Sum('quantity')).order_by('-count')[:6]
    )

    # last 7 days chart
    chart = []
    for offset in range(6, -1, -1):
        day = (now - timedelta(days=offset)).date()
        day_orders = orders.filter(created_at__date=day)
        chart.append({
            'label': day.strftime('%d/%m'),
            'count': day_orders.count(),
            'total': float(day_orders.aggregate(t=Sum('total'))['t'] or 0),
        })
    max_total = max([c['total'] for c in chart] + [1])
    for point in chart:
        point['height'] = round(point['total'] / max_total * 100)

    top_products = (
        Product.objects.annotate(sold=Sum('order_items__quantity'))
        .filter(sold__gt=0).order_by('-sold')[:5]
    )

    review_stats = Review.objects.filter(is_approved=True).aggregate(a=Avg('rating'), c=Count('id'))
    context = {
        'perms': staff_permissions(request.user),
        'awaiting_payments': orders.filter(payment_status='pending').exclude(status='cancelled')[:5],
        'latest_reviews': Review.objects.select_related('user')[:4],
        'stats': {
            'customers': User.objects.filter(is_staff=False).count(),
            'new_customers': User.objects.filter(is_staff=False, date_joined__gte=month_ago).count(),
            'works': Work.objects.filter(is_active=True).count(),
            'reviews': review_stats['c'] or 0,
            'rating': round(review_stats['a'] or 0, 1),
            'paid_online': orders.filter(payment_method='paypal', payment_status='paid').count(),
            'orders': orders.count(),
            'pending': orders.filter(status='pending').count(),
            'delivered': orders.filter(status='delivered').count(),
            'revenue': revenue,
            'month_revenue': month_revenue,
            'products': Product.objects.count(),
            'active_products': Product.objects.filter(is_active=True).count(),
            'categories': Category.objects.count(),
            'coupons': Coupon.objects.filter(is_active=True).count(),
            'week_orders': orders.filter(created_at__gte=week_ago).count(),
        },
        'recent_orders': orders.select_related('country')[:8],
        'top_services': top_services,
        'services_count': Service.objects.count(),
        'top_products': top_products,
        'chart': chart,
        'active_page': 'index',
        **_pending_counts(),
    }
    return render(request, 'dashboard/index.html', context)


# ================================================================== products
@perm_required('products')
def product_list(request):
    query = (request.GET.get('q') or '').strip()
    category = request.GET.get('category') or ''
    status = request.GET.get('status') or ''

    products = (
        Product.objects.select_related('category')
        .prefetch_related('images')
        .annotate(services_count=Count('variants__service', distinct=True))
        .order_by('ordering', '-created_at')
    )
    if query:
        products = products.filter(
            Q(name_ar__icontains=query) | Q(name_en__icontains=query) | Q(sku__icontains=query)
        )
    if category.isdigit():
        products = products.filter(category_id=int(category))
    if status == 'active':
        products = products.filter(is_active=True)
    elif status == 'hidden':
        products = products.filter(is_active=False)
    elif status == 'no_services':
        products = products.filter(services_count=0)

    context = {
        'page_obj': _paginate(request, products),
        'categories': Category.objects.all(),
        'q': query, 'category': category, 'status': status,
        'active_page': 'products',
        **_pending_counts(),
    }
    return render(request, 'dashboard/products/list.html', context)


@perm_required('products')
def product_form(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else None
    form = ProductForm(request.POST or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        obj = form.save()
        if product is None:
            # a new design starts with every available service switched on
            obj.sync_variants(Service.objects.filter(is_active=True).values_list('id', flat=True))
        messages.success(request, 'تم حفظ المنتج بنجاح')
        if 'save_and_media' in request.POST or product is None:
            return redirect('dash_product_media', pk=obj.pk)
        return redirect('dash_products')
    context = {
        'form': form,
        # an invalid form edits the instance in memory (e.g. an emptied slug) — show the saved row
        'product': Product.objects.get(pk=product.pk) if product else None,
        'active_page': 'products',
        **_pending_counts(),
    }
    return render(request, 'dashboard/products/form.html', context)


@perm_required('products')
def product_media(request, pk):
    """Colors + images for one product."""
    product = get_object_or_404(Product, pk=pk)
    color_form = ColorForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_color':
            color_form = ColorForm(request.POST)
            if color_form.is_valid():
                color = color_form.save(commit=False)
                color.product = product
                color.save()
                product.sync_variants()
                messages.success(request, 'تمت إضافة اللون')
                return redirect('dash_product_media', pk=product.pk)

        elif action == 'edit_color':
            color = get_object_or_404(ProductColor, pk=request.POST.get('color_id'), product=product)
            color.name_ar = request.POST.get('name_ar') or color.name_ar
            color.name_en = request.POST.get('name_en') or ''
            color.hex_code = request.POST.get('hex_code') or color.hex_code
            color.save()
            messages.success(request, 'تم تحديث اللون')
            return redirect('dash_product_media', pk=product.pk)

        elif action == 'upload_images':
            files = request.FILES.getlist('images')
            color_id = request.POST.get('color') or ''
            color = product.colors.filter(pk=color_id).first() if color_id.isdigit() else None
            created = 0
            for index, image in enumerate(files):
                ProductImage.objects.create(
                    product=product, color=color, image=image,
                    ordering=product.images.count() + index,
                    is_main=not product.images.filter(is_main=True).exists() and index == 0,
                )
                created += 1
            messages.success(request, f'تم رفع {created} صورة')
            return redirect('dash_product_media', pk=product.pk)

    context = {
        'product': product,
        'colors': product.colors.all(),
        'images': product.images.select_related('color'),
        'color_form': color_form,
        'active_page': 'products',
        **_pending_counts(),
    }
    return render(request, 'dashboard/products/media.html', context)


@perm_required('products')
def product_services(request, pk):
    """Which services this design is offered with (colour × service, no stock)."""
    product = get_object_or_404(Product, pk=pk)
    services = list(Service.objects.all())

    if request.method == 'POST':
        chosen = {int(s) for s in request.POST.getlist('services') if s.isdigit()}
        product.sync_variants([s.id for s in services if s.id in chosen])
        messages.success(request, 'تم حفظ خدمات المنتج')
        return redirect('dash_product_services', pk=product.pk)

    selected = product.selected_service_ids
    context = {
        'product': product,
        'services': services,
        'selected_ids': selected,
        'colors': product.colors.all(),
        'active_page': 'products',
        **_pending_counts(),
    }
    return render(request, 'dashboard/products/services.html', context)


@perm_required('products')
def product_stock_redirect(request, pk):
    """Old «المقاسات والكميات» link → the design's services page."""
    return redirect('dash_product_services', pk=pk)


@perm_required('products')
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, 'تم حذف المنتج')
    return redirect('dash_products')


@perm_required('products')
def product_toggle(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save(update_fields=['is_active'])
    return redirect(request.META.get('HTTP_REFERER', 'dash_products'))


@perm_required('products')
@require_POST
def color_delete(request, pk):
    color = get_object_or_404(ProductColor, pk=pk)
    product = color.product
    color.delete()
    product.sync_variants()
    product_id = product.pk
    messages.info(request, 'تم حذف اللون')
    return redirect('dash_product_media', pk=product_id)


@perm_required('products')
@require_POST
def image_delete(request, pk):
    image = get_object_or_404(ProductImage, pk=pk)
    product_id = image.product_id
    image.delete()
    messages.info(request, 'تم حذف الصورة')
    return redirect('dash_product_media', pk=product_id)


@perm_required('products')
def image_main(request, pk):
    image = get_object_or_404(ProductImage, pk=pk)
    ProductImage.objects.filter(product=image.product).update(is_main=False)
    ProductImage.objects.filter(pk=image.pk).update(is_main=True)
    return redirect('dash_product_media', pk=image.product_id)


# ================================================================ categories
@perm_required('products')
def category_list(request):
    categories = Category.objects.annotate(count=Count('products'))
    return render(request, 'dashboard/categories/list.html', {
        'categories': categories, 'active_page': 'categories', **_pending_counts(),
    })


@perm_required('products')
def category_form(request, pk=None):
    category = get_object_or_404(Category, pk=pk) if pk else None
    form = CategoryForm(request.POST or None, request.FILES or None, instance=category)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ القسم')
        return redirect('dash_categories')
    return render(request, 'dashboard/categories/form.html', {
        'form': form, 'object': category, 'active_page': 'categories', **_pending_counts(),
    })


@perm_required('products')
@require_POST
def category_delete(request, pk):
    get_object_or_404(Category, pk=pk).delete()
    messages.info(request, 'تم حذف القسم')
    return redirect('dash_categories')


# ================================================================== services
@perm_required('products')
def service_list(request, pk=None):
    """Malak writes the services here (they replaced the clothing sizes)."""
    service = get_object_or_404(Service, pk=pk) if pk else None
    form = ServiceForm(request.POST or None, instance=service)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            obj = form.save()
            if service is None and form.cleaned_data.get('add_to_all'):
                for product in Product.objects.prefetch_related('colors', 'variants'):
                    product.sync_variants(product.selected_service_ids | {obj.pk})
        messages.success(request, 'تم حفظ الخدمة' if service else 'تمت إضافة الخدمة')
        return redirect('dash_services')
    services = Service.objects.annotate(
        designs=Count('variants__product', distinct=True),
    )
    return render(request, 'dashboard/services/list.html', {
        'services': services, 'form': form, 'object': service,
        'products_total': Product.objects.count(),
        'active_page': 'services', **_pending_counts(),
    })


@perm_required('products')
@require_POST
def service_toggle(request, pk):
    service = get_object_or_404(Service, pk=pk)
    service.is_active = not service.is_active
    service.save(update_fields=['is_active'])
    return redirect('dash_services')


@perm_required('products')
@require_POST
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    products = list(Product.objects.filter(variants__service=service).distinct())
    with transaction.atomic():
        service.delete()
        for product in products:
            product.sync_variants()  # a design left with no service stays orderable by colour
    messages.info(request, 'تم حذف الخدمة')
    return redirect('dash_services')


def sizes_redirect(request, pk=None):
    return redirect('dash_services')


# ==================================================================== orders
@perm_required('orders')
def order_list(request):
    query = (request.GET.get('q') or '').strip()
    status = request.GET.get('status') or ''
    orders = Order.objects.select_related('country').prefetch_related('items')
    if query:
        orders = orders.filter(
            Q(order_number__icontains=query) | Q(full_name__icontains=query)
            | Q(phone__icontains=query)
        )
    if status:
        orders = orders.filter(status=status)
    payment = request.GET.get('payment') or ''
    if payment:
        orders = orders.filter(payment_status=payment)
    return render(request, 'dashboard/orders/list.html', {
        'page_obj': _paginate(request, orders),
        'q': query, 'status': status, 'payment': payment,
        'statuses': Order.STATUSES,
        'payment_statuses': PAYMENT_STATUSES,
        'active_page': 'orders', **_pending_counts(),
    })


@perm_required('orders')
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('country', 'coupon').prefetch_related('items'), pk=pk
    )
    if request.method == 'POST':
        order.admin_note = request.POST.get('admin_note') or ''
        order.save(update_fields=['admin_note'])
        messages.success(request, 'تم حفظ الملاحظة')
        return redirect('dash_order_detail', pk=order.pk)
    return render(request, 'dashboard/orders/detail.html', {
        'order': order, 'statuses': Order.STATUSES, 'payment_statuses': PAYMENT_STATUSES,
        'active_page': 'orders', **_pending_counts(),
    })


@perm_required('orders')
@require_POST
def order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    status = request.POST.get('status')
    if status in dict(Order.STATUSES):
        order.status = status
        fields = ['status', 'updated_at']
        # cash is collected on delivery → the order counts as paid
        if status == 'delivered' and order.payment_method == 'cod' and not order.is_paid:
            order.payment_status = 'paid'
            order.paid_at = timezone.now()
            fields += ['payment_status', 'paid_at']
        order.save(update_fields=fields)
        messages.success(request, 'تم تحديث حالة الطلب')
    return redirect(request.META.get('HTTP_REFERER') or 'dash_orders')


@perm_required('orders')
@require_POST
def order_payment(request, pk):
    """Confirm / change the payment status (PayPal link payments are confirmed by hand)."""
    order = get_object_or_404(Order, pk=pk)
    status = request.POST.get('payment_status')
    if status == 'paid':
        order.mark_paid()
        messages.success(request, 'تم تأكيد الدفع — العميل يقدر يقيّم دلوقتي')
    elif status in ('unpaid', 'pending', 'failed', 'refunded'):
        order.payment_status = status
        if status != 'refunded':
            order.paid_at = None
        order.save(update_fields=['payment_status', 'paid_at', 'updated_at'])
        messages.success(request, 'تم تحديث حالة الدفع')
    return redirect(request.META.get('HTTP_REFERER') or 'dash_orders')


@perm_required('orders')
@require_POST
def order_delete(request, pk):
    get_object_or_404(Order, pk=pk).delete()
    messages.info(request, 'تم حذف الطلب')
    return redirect('dash_orders')


@perm_required('orders')
def order_print(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('country').prefetch_related('items'), pk=pk
    )
    return render(request, 'dashboard/orders/print.html', {'order': order})


# =================================================================== coupons
@perm_required('marketing')
def coupon_list(request):
    return render(request, 'dashboard/coupons/list.html', {
        'coupons': Coupon.objects.all(), 'active_page': 'coupons', **_pending_counts(),
    })


@perm_required('marketing')
def coupon_form(request, pk=None):
    coupon = get_object_or_404(Coupon, pk=pk) if pk else None
    form = CouponForm(request.POST or None, instance=coupon)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ كود الخصم')
        return redirect('dash_coupons')
    return render(request, 'dashboard/coupons/form.html', {
        'form': form, 'object': coupon, 'active_page': 'coupons', **_pending_counts(),
    })


@perm_required('marketing')
@require_POST
def coupon_delete(request, pk):
    get_object_or_404(Coupon, pk=pk).delete()
    messages.info(request, 'تم حذف الكود')
    return redirect('dash_coupons')


# ================================================================ promotions
@perm_required('marketing')
def promotion_list(request):
    return render(request, 'dashboard/promotions/list.html', {
        'promotions': Promotion.objects.prefetch_related('categories', 'products'),
        'active_page': 'promotions', **_pending_counts(),
    })


@perm_required('marketing')
def promotion_form(request, pk=None):
    promotion = get_object_or_404(Promotion, pk=pk) if pk else None
    form = PromotionForm(request.POST or None, instance=promotion)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ العرض')
        return redirect('dash_promotions')
    return render(request, 'dashboard/promotions/form.html', {
        'form': form, 'object': promotion, 'active_page': 'promotions', **_pending_counts(),
    })


@perm_required('marketing')
@require_POST
def promotion_delete(request, pk):
    get_object_or_404(Promotion, pk=pk).delete()
    messages.info(request, 'تم حذف العرض')
    return redirect('dash_promotions')


# ============================================================= announcements
@perm_required('content')
def announcement_list(request):
    return render(request, 'dashboard/announcements/list.html', {
        'announcements': Announcement.objects.all(),
        'active_page': 'announcements', **_pending_counts(),
    })


@perm_required('content')
def announcement_form(request, pk=None):
    obj = get_object_or_404(Announcement, pk=pk) if pk else None
    form = AnnouncementForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ الإعلان')
        return redirect('dash_announcements')
    return render(request, 'dashboard/announcements/form.html', {
        'form': form, 'object': obj, 'active_page': 'announcements', **_pending_counts(),
    })


@perm_required('content')
@require_POST
def announcement_delete(request, pk):
    get_object_or_404(Announcement, pk=pk).delete()
    messages.info(request, 'تم حذف الإعلان')
    return redirect('dash_announcements')


# =================================================================== banners
@perm_required('content')
def banner_list(request):
    return render(request, 'dashboard/banners/list.html', {
        'banners': Banner.objects.all(), 'active_page': 'banners', **_pending_counts(),
    })


@perm_required('content')
def banner_form(request, pk=None):
    obj = get_object_or_404(Banner, pk=pk) if pk else None
    form = BannerForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ البانر')
        return redirect('dash_banners')
    return render(request, 'dashboard/banners/form.html', {
        'form': form, 'object': obj, 'active_page': 'banners', **_pending_counts(),
    })


@perm_required('content')
@require_POST
def banner_delete(request, pk):
    get_object_or_404(Banner, pk=pk).delete()
    messages.info(request, 'تم حذف البانر')
    return redirect('dash_banners')


# ================================================================= countries
def _arabic_key(text):
    """Sort Arabic names the way people expect (أ / إ / آ = ا)."""
    text = (text or '').strip()
    for a in 'أإآ':
        text = text.replace(a, 'ا')
    return text


def _parse_amount(raw):
    """'' -> None (use the general value), otherwise a non-negative Decimal. Raises ValueError."""
    raw = (raw or '').strip().replace(',', '')
    if raw == '':
        return None
    value = Decimal(raw)
    if value < 0 or value >= Decimal('100000000'):
        raise ValueError
    return value.quantize(Decimal('0.01'))


def _countries_back(request):
    target = request.POST.get('next') or ''
    return target if target.startswith('/dashboard/countries/') else reverse('dash_countries')


@perm_required('shipping')
def country_list(request):
    show = request.GET.get('show') or 'all'
    everything = list(Country.objects.all())
    counts = {
        'all': len(everything),
        'active': sum(1 for c in everything if c.is_active),
    }
    counts['inactive'] = counts['all'] - counts['active']
    countries = everything
    if show == 'active':
        countries = [c for c in everything if c.is_active]
    elif show == 'inactive':
        countries = [c for c in everything if not c.is_active]
    else:
        show = 'all'
    countries.sort(key=lambda c: (not c.is_active, c.ordering, _arabic_key(c.name_ar)))
    return render(request, 'dashboard/countries/list.html', {
        'countries': countries, 'show': show, 'counts': counts,
        'site': SiteSettings.load(),
        'active_page': 'countries', **_pending_counts(),
    })


@perm_required('shipping')
def country_form(request, pk=None):
    obj = get_object_or_404(Country, pk=pk) if pk else None
    form = CountryForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        country = form.save()
        messages.success(request, f'تم حفظ {country.name_ar}')
        return redirect('dash_countries')
    return render(request, 'dashboard/countries/form.html', {
        'form': form, 'object': obj, 'site': SiteSettings.load(),
        'active_page': 'countries', **_pending_counts(),
    })


@perm_required('shipping')
@require_POST
def country_toggle(request, pk):
    country = get_object_or_404(Country, pk=pk)
    country.is_active = not country.is_active
    country.save(update_fields=['is_active'])
    if country.is_active:
        messages.success(request, f'{country.name_ar}: الشحن متاح')
    else:
        messages.info(request, f'{country.name_ar}: الشحن اتقفل')
    return redirect(_countries_back(request))


@perm_required('shipping')
@require_POST
def country_fee(request, pk):
    country = get_object_or_404(Country, pk=pk)
    try:
        country.shipping_fee = _parse_amount(request.POST.get('shipping_fee'))
    except (ValueError, ArithmeticError):
        messages.error(request, 'اكتب سعر شحن صحيح')
        return redirect(_countries_back(request))
    country.save(update_fields=['shipping_fee'])
    messages.success(request, f'تم حفظ سعر الشحن لـ {country.name_ar}')
    return redirect(_countries_back(request))


@perm_required('shipping')
@require_POST
def country_bulk(request):
    ids = [int(i) for i in request.POST.getlist('ids') if i.isdigit()]
    action = request.POST.get('action') or ''
    countries = Country.objects.filter(pk__in=ids)
    if not ids or not countries.exists():
        messages.error(request, 'اختار دولة واحدة على الأقل')
        return redirect(_countries_back(request))
    count = countries.count()
    if action == 'activate':
        countries.update(is_active=True)
        messages.success(request, f'اتفتح الشحن لـ {count} دولة')
    elif action == 'deactivate':
        countries.update(is_active=False)
        messages.info(request, f'اتقفل الشحن لـ {count} دولة')
    elif action == 'fee':
        try:
            fee = _parse_amount(request.POST.get('fee'))
        except (ValueError, ArithmeticError):
            messages.error(request, 'اكتب سعر شحن صحيح')
            return redirect(_countries_back(request))
        countries.update(shipping_fee=fee)
        messages.success(request, f'اتحدّث سعر الشحن لـ {count} دولة')
    elif action == 'delete':
        countries.delete()
        messages.info(request, f'اتحذف {count} دولة')
    else:
        messages.error(request, 'اختار الإجراء')
    return redirect(_countries_back(request))


@perm_required('shipping')
@require_POST
def country_delete(request, pk):
    country = get_object_or_404(Country, pk=pk)
    country.delete()
    messages.info(request, f'تم حذف {country.name_ar}')
    return redirect(_countries_back(request))


# ================================================================== messages
@perm_required('messages')
def message_list(request):
    return render(request, 'dashboard/messages/list.html', {
        'items': _paginate(request, ContactMessage.objects.all()),
        'active_page': 'messages', **_pending_counts(),
    })


@perm_required('messages')
def message_detail(request, pk):
    item = get_object_or_404(ContactMessage, pk=pk)
    if not item.is_read:
        item.is_read = True
        item.save(update_fields=['is_read'])
    return render(request, 'dashboard/messages/detail.html', {
        'item': item, 'active_page': 'messages', **_pending_counts(),
    })


@perm_required('messages')
@require_POST
def message_delete(request, pk):
    get_object_or_404(ContactMessage, pk=pk).delete()
    messages.info(request, 'تم حذف الرسالة')
    return redirect('dash_messages')


# =================================================================== tickets
@perm_required('messages')
def ticket_list(request):
    status = request.GET.get('status') or ''
    query = (request.GET.get('q') or '').strip()
    tickets = Ticket.objects.select_related('user', 'order').annotate(n=Count('messages'))
    if status in dict(TICKET_STATUSES):
        tickets = tickets.filter(status=status)
    elif status == 'unread':
        tickets = tickets.filter(admin_unread=True).exclude(status='closed')
    if query:
        tickets = tickets.filter(
            Q(number__icontains=query) | Q(subject__icontains=query)
            | Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query)
            | Q(user__email__icontains=query)
        )
    counts = {
        'all': Ticket.objects.count(),
        'open': Ticket.objects.filter(status='open').count(),
        'answered': Ticket.objects.filter(status='answered').count(),
        'closed': Ticket.objects.filter(status='closed').count(),
    }
    return render(request, 'dashboard/tickets/list.html', {
        'page_obj': _paginate(request, tickets), 'status': status, 'q': query, 'counts': counts,
        'active_page': 'tickets', **_pending_counts(),
    })


@perm_required('messages')
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket.objects.select_related('user', 'order'), pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action') or 'reply'
        if action == 'status':
            new_status = request.POST.get('status') or ''
            if new_status in dict(TICKET_STATUSES):
                ticket.status = new_status
                ticket.save(update_fields=['status', 'updated_at'])
                messages.success(request, f'الحالة بقت: {ticket.status_label}')
            return redirect('dash_ticket_detail', pk=ticket.pk)

        body = (request.POST.get('body') or '').strip()
        files = ticket_uploads(request)
        if not body and not files:
            messages.error(request, 'اكتب ردًا أو ارفع ملف')
            return redirect('dash_ticket_detail', pk=ticket.pk)
        with transaction.atomic():
            message = TicketMessage.objects.create(
                ticket=ticket, author=request.user, is_staff=True, body=body[:4000],
            )
            rejected = save_ticket_attachments(message, files)
            ticket.touch(from_staff=True)
        if rejected:
            messages.warning(request, 'ملفات ما اتبعتش: ' + '، '.join(rejected[:3]))
        mailer.ticket_staff_replied(ticket, message)
        messages.success(request, 'تم إرسال الرد للعميل')
        return redirect('dash_ticket_detail', pk=ticket.pk)

    if ticket.admin_unread:
        Ticket.objects.filter(pk=ticket.pk).update(admin_unread=False)
        ticket.admin_unread = False
    return render(request, 'dashboard/tickets/detail.html', {
        'ticket': ticket,
        'ticket_messages': ticket.messages.prefetch_related('attachments').select_related('author'),
        'statuses': TICKET_STATUSES,
        'max_files': TICKET_MAX_FILES, 'max_mb': TICKET_MAX_FILE_MB,
        'orders': ticket.user.orders.order_by('-created_at')[:5],
        'active_page': 'tickets', **_pending_counts(),
    })


@perm_required('messages')
@require_POST
def ticket_delete(request, pk):
    get_object_or_404(Ticket, pk=pk).delete()
    messages.info(request, 'تم حذف التذكرة')
    return redirect('dash_tickets')


# ============================================================= notifications
@perm_required('settings')
def notification_settings(request):
    site = SiteSettings.load()
    form = NotificationSettingsForm(request.POST or None, instance=site)
    if request.method == 'POST':
        if request.POST.get('action') == 'test':
            target = (request.POST.get('test_email') or site.notify_email or site.smtp_user).strip()
            if not site.mail_ready:
                messages.error(request, 'شغّل الإيميلات واكتب بيانات SMTP والباسورد الأول')
            else:
                ok, error = mailer.send_test(site, target)
                if ok:
                    messages.success(request, f'اتبعت إيميل تجربة لـ {target} — شوف الإنبوكس')
                else:
                    messages.error(request, f'ما اتبعتش: {error}')
            return redirect('dash_notifications')
        if form.is_valid():
            form.save()
            messages.success(request, 'تم حفظ إعدادات الإشعارات')
            return redirect('dash_notifications')

    return render(request, 'dashboard/notifications.html', {
        'form': form, 'site': site, 'active_page': 'notifications', **_pending_counts(),
    })


# ================================================================== settings
@perm_required('settings')
def settings_view(request):
    site = SiteSettings.load()
    form = SiteSettingsForm(request.POST or None, request.FILES or None, instance=site)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ الإعدادات')
        return redirect('dash_settings')
    return render(request, 'dashboard/settings.html', {
        'form': form, 'site': site, 'active_page': 'settings', **_pending_counts(),
    })


@perm_required('settings')
def payment_settings(request):
    site = SiteSettings.load()
    form = PaymentSettingsForm(request.POST or None, instance=site)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ إعدادات الدفع')
        return redirect('dash_payments')
    return render(request, 'dashboard/payments.html', {
        'form': form, 'site': site, 'active_page': 'payments', **_pending_counts(),
    })


@perm_required('settings')
def google_settings(request):
    """«الدخول بجوجل» — المفاتيح + اللينكات اللي Google Cloud محتاجها."""
    site = SiteSettings.load()
    form = GoogleLoginForm(request.POST or None, instance=site)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ إعدادات الدخول بجوجل')
        return redirect('dash_google')

    redirect_uri = google_oauth.redirect_uri(request, site)
    origin = redirect_uri.split('/account/')[0]
    return render(request, 'dashboard/google.html', {
        'form': form, 'site': site,
        'redirect_uri': redirect_uri,
        'origin': origin,
        'google_users': CustomerProfile.objects.exclude(google_id='').count(),
        'active_page': 'google', **_pending_counts(),
    })


# ================================================================= customers
def _customers_queryset():
    return (
        User.objects.filter(is_staff=False)
        .select_related('customer', 'customer__country')
        .annotate(
            n_orders=Count('orders', distinct=True),
            spent=Sum('orders__total', filter=Q(orders__payment_status='paid')),
            last_order=Max('orders__created_at'),
        )
    )


@perm_required('customers')
def customer_list(request):
    query = (request.GET.get('q') or '').strip()
    sort = request.GET.get('sort') or 'new'
    customers = _customers_queryset()
    if query:
        customers = customers.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
            | Q(email__icontains=query) | Q(customer__phone__icontains=query)
            | Q(customer__city__icontains=query)
        )
    sorts = {
        'new': '-date_joined', 'old': 'date_joined', 'orders': '-n_orders',
        'spent': F('spent').desc(nulls_last=True), 'name': 'first_name',
        'last': F('last_order').desc(nulls_last=True),
    }
    customers = customers.order_by(sorts.get(sort, '-date_joined'))
    all_customers = User.objects.filter(is_staff=False)
    month_ago = timezone.now() - timedelta(days=30)
    return render(request, 'dashboard/customers/list.html', {
        'page_obj': _paginate(request, customers),
        'q': query, 'sort': sort,
        'stats': {
            'total': all_customers.count(),
            'new': all_customers.filter(date_joined__gte=month_ago).count(),
            'buyers': all_customers.filter(orders__isnull=False).distinct().count(),
        },
        'active_page': 'customers', **_pending_counts(),
    })


@perm_required('customers')
def customer_export(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="customers.csv"'
    response.write('﻿')  # Excel opens Arabic correctly with a BOM
    writer = csv.writer(response)
    writer.writerow(['الاسم', 'البريد الإلكتروني', 'الموبايل', 'موبايل آخر', 'الدولة',
                     'المدينة', 'العنوان', 'عدد الطلبات', 'إجمالي المدفوع', 'تاريخ التسجيل'])
    for user in _customers_queryset().order_by('-date_joined'):
        profile = getattr(user, 'customer', None)
        writer.writerow([
            user.get_full_name(), user.email,
            profile.phone if profile else '', profile.phone_alt if profile else '',
            profile.country.name_ar if profile and profile.country else '',
            profile.city if profile else '', profile.address if profile else '',
            user.n_orders, user.spent or 0, user.date_joined.strftime('%Y-%m-%d'),
        ])
    return response


@perm_required('customers')
def customer_detail(request, pk):
    customer = get_object_or_404(User.objects.select_related('customer'), pk=pk, is_staff=False)
    profile = CustomerProfile.for_user(customer)
    if request.method == 'POST':
        profile.admin_note = request.POST.get('admin_note') or ''
        profile.save(update_fields=['admin_note', 'updated_at'])
        messages.success(request, 'تم حفظ الملاحظة')
        return redirect('dash_customer_detail', pk=customer.pk)
    orders = customer.orders.select_related('country').prefetch_related('items')
    totals = orders.aggregate(
        n=Count('id'),
        paid=Sum('total', filter=Q(payment_status='paid')),
        all=Sum('total'),
    )
    return render(request, 'dashboard/customers/detail.html', {
        'customer': customer, 'profile': profile, 'orders': orders,
        'reviews': customer.reviews.all(), 'totals': totals,
        'active_page': 'customers', **_pending_counts(),
    })


@perm_required('customers')
@require_POST
def customer_toggle(request, pk):
    customer = get_object_or_404(User, pk=pk, is_staff=False)
    customer.is_active = not customer.is_active
    customer.save(update_fields=['is_active'])
    messages.success(request, 'تم تفعيل الحساب' if customer.is_active else 'تم إيقاف الحساب')
    return redirect('dash_customer_detail', pk=customer.pk)


@perm_required('customers')
@require_POST
def customer_delete(request, pk):
    customer = get_object_or_404(User, pk=pk, is_staff=False)
    customer.delete()  # orders stay (their user becomes empty)
    messages.info(request, 'تم حذف حساب العميل — طلباته لسه موجودة')
    return redirect('dash_customers')


# ================================================================= portfolio
@perm_required('portfolio')
def work_list(request):
    works = Work.objects.select_related('category').annotate(n_media=Count('media')).order_by('ordering', '-created_at')
    cat = request.GET.get('cat') or ''
    if cat.isdigit():
        works = works.filter(category_id=int(cat))
    return render(request, 'dashboard/works/list.html', {
        'works': works, 'categories': WorkCategory.objects.all(), 'cat': cat,
        'active_page': 'works', **_pending_counts(),
    })


@perm_required('portfolio')
def work_form(request, pk=None):
    work = get_object_or_404(Work, pk=pk) if pk else None
    form = WorkForm(request.POST or None, request.FILES or None, instance=work)
    if request.method == 'POST' and form.is_valid():
        obj = form.save()
        messages.success(request, 'تم حفظ العمل')
        if work is None or 'save_and_media' in request.POST:
            return redirect('dash_work_media', pk=obj.pk)
        return redirect('dash_works')
    return render(request, 'dashboard/works/form.html', {
        'form': form, 'object': Work.objects.get(pk=work.pk) if work else None,
        'active_page': 'works', **_pending_counts(),
    })


@perm_required('portfolio')
def work_media(request, pk):
    work = get_object_or_404(Work, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        start = (work.media.aggregate(m=Max('ordering'))['m'] or 0) + 1
        if action == 'upload_images':
            files = request.FILES.getlist('images')
            ok = 0
            for index, image in enumerate(files):
                if not (image.content_type or '').startswith('image/'):
                    continue
                WorkMedia.objects.create(work=work, kind='image', image=image, ordering=start + index)
                ok += 1
            messages.success(request, f'تم رفع {ok} صورة') if ok else messages.error(request, 'اختار صور بس')
        elif action == 'upload_video':
            video = request.FILES.get('video')
            ext = (video.name.rsplit('.', 1)[-1].lower() if video else '')
            if not video or ext not in ('mp4', 'webm', 'mov', 'm4v'):
                messages.error(request, 'ارفع فيديو بصيغة MP4 أو WEBM أو MOV')
            else:
                WorkMedia.objects.create(
                    work=work, kind='video', video=video, poster=request.FILES.get('poster'),
                    caption_ar=(request.POST.get('caption_ar') or '')[:200],
                    caption_en=(request.POST.get('caption_en') or '')[:200],
                    ordering=start,
                )
                messages.success(request, 'تم رفع الفيديو')
        elif action == 'add_embed':
            url = (request.POST.get('embed_url') or '').strip()
            media = WorkMedia(work=work, kind='embed', embed_url=url, ordering=start,
                              caption_ar=(request.POST.get('caption_ar') or '')[:200],
                              caption_en=(request.POST.get('caption_en') or '')[:200])
            if not url.startswith('http') or not (('youtu' in url) or ('vimeo' in url)):
                messages.error(request, 'حط لينك يوتيوب أو فيميو صحيح')
            else:
                if request.FILES.get('poster'):
                    media.poster = request.FILES['poster']
                media.save()
                messages.success(request, 'تمت إضافة الفيديو')
        elif action == 'save_items':
            for media in work.media.all():
                prefix = f'm{media.pk}_'
                if prefix + 'order' not in request.POST:
                    continue
                try:
                    media.ordering = max(0, int(request.POST.get(prefix + 'order') or 0))
                except ValueError:
                    pass
                media.caption_ar = (request.POST.get(prefix + 'caption_ar') or '')[:200]
                media.caption_en = (request.POST.get(prefix + 'caption_en') or '')[:200]
                poster = request.FILES.get(prefix + 'poster')
                if poster and media.is_video:
                    media.poster = poster
                media.save()
            messages.success(request, 'تم حفظ الترتيب والتعليقات')
        return redirect('dash_work_media', pk=work.pk)

    return render(request, 'dashboard/works/media.html', {
        'work': work, 'media': work.media.all(),
        'active_page': 'works', **_pending_counts(),
    })


@perm_required('portfolio')
@require_POST
def work_toggle(request, pk, field):
    work = get_object_or_404(Work, pk=pk)
    if field in ('is_active', 'is_featured'):
        setattr(work, field, not getattr(work, field))
        work.save(update_fields=[field, 'updated_at'])
    return redirect(request.META.get('HTTP_REFERER') or 'dash_works')


@perm_required('portfolio')
@require_POST
def work_delete(request, pk):
    get_object_or_404(Work, pk=pk).delete()
    messages.info(request, 'تم حذف العمل')
    return redirect('dash_works')


@perm_required('portfolio')
@require_POST
def work_media_delete(request, pk):
    media = get_object_or_404(WorkMedia, pk=pk)
    work_id = media.work_id
    media.delete()
    messages.info(request, 'تم الحذف')
    return redirect('dash_work_media', pk=work_id)


@perm_required('portfolio')
@require_POST
def work_media_cover(request, pk):
    """Use an uploaded photo as the work's banner."""
    media = get_object_or_404(WorkMedia, pk=pk, kind='image')
    work = media.work
    work.cover = media.image.name
    work.save(update_fields=['cover', 'updated_at'])
    messages.success(request, 'بقت صورة الغلاف / البانر')
    return redirect('dash_work_media', pk=work.pk)


@perm_required('portfolio')
def work_category_list(request):
    edit = None
    if request.GET.get('edit', '').isdigit():
        edit = WorkCategory.objects.filter(pk=int(request.GET['edit'])).first()
    form = WorkCategoryForm(request.POST or None, instance=edit)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ التصنيف')
        return redirect('dash_work_categories')
    return render(request, 'dashboard/works/categories.html', {
        'categories': WorkCategory.objects.annotate(n=Count('works')).order_by('ordering', 'id'),
        'form': form, 'edit': edit,
        'active_page': 'works', **_pending_counts(),
    })


@perm_required('portfolio')
@require_POST
def work_category_delete(request, pk):
    get_object_or_404(WorkCategory, pk=pk).delete()
    messages.info(request, 'تم حذف التصنيف')
    return redirect('dash_work_categories')


# =================================================================== reviews
@perm_required('reviews')
def review_list(request):
    status = request.GET.get('status') or ''
    rating = request.GET.get('rating') or ''
    query = (request.GET.get('q') or '').strip()
    items = Review.objects.select_related('user', 'order')
    if status == 'pending':
        items = items.filter(is_approved=False)
    elif status == 'published':
        items = items.filter(is_approved=True)
    elif status == 'featured':
        items = items.filter(is_featured=True)
    if rating.isdigit():
        items = items.filter(rating=int(rating))
    if query:
        items = items.filter(Q(name__icontains=query) | Q(comment__icontains=query))
    summary = Review.summary()
    return render(request, 'dashboard/reviews/list.html', {
        'page_obj': _paginate(request, items),
        'status': status, 'rating': rating, 'q': query,
        'summary': summary,
        'counts': {
            'all': Review.objects.count(),
            'pending': Review.objects.filter(is_approved=False).count(),
            'published': Review.objects.filter(is_approved=True).count(),
            'featured': Review.objects.filter(is_featured=True).count(),
        },
        'auto_publish': SiteSettings.load().reviews_auto_publish,
        'active_page': 'reviews', **_pending_counts(),
    })


@perm_required('reviews')
def review_edit(request, pk):
    review = get_object_or_404(Review.objects.select_related('user', 'order'), pk=pk)
    form = ReviewForm(request.POST or None, instance=review)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ التقييم')
        return redirect('dash_reviews')
    return render(request, 'dashboard/reviews/form.html', {
        'form': form, 'review': review, 'active_page': 'reviews', **_pending_counts(),
    })


@perm_required('reviews')
@require_POST
def review_toggle(request, pk, field):
    review = get_object_or_404(Review, pk=pk)
    if field in ('is_approved', 'is_featured'):
        setattr(review, field, not getattr(review, field))
        if field == 'is_featured' and review.is_featured:
            review.is_approved = True
        review.save(update_fields=['is_approved', 'is_featured', 'updated_at'])
    return redirect(request.META.get('HTTP_REFERER') or 'dash_reviews')


@perm_required('reviews')
@require_POST
def review_delete(request, pk):
    get_object_or_404(Review, pk=pk).delete()
    messages.info(request, 'تم حذف التقييم')
    return redirect(request.META.get('HTTP_REFERER') or 'dash_reviews')


# ============================================================ homepage / nav
def _swap(model, obj, direction, scope=None):
    """Move `obj` one step up/down by rewriting a clean 0..n ordering."""
    items = list(scope if scope is not None else model.objects.all())
    if obj not in items:
        return
    i = items.index(obj)
    j = i - 1 if direction == 'up' else i + 1
    if 0 <= j < len(items):
        items[i], items[j] = items[j], items[i]
    for index, item in enumerate(items):
        if item.ordering != index:
            model.objects.filter(pk=item.pk).update(ordering=index)


@perm_required('content')
def home_sections(request):
    HomeSection.ensure_defaults()
    return render(request, 'dashboard/homepage/list.html', {
        'sections': HomeSection.objects.all(),
        'active_page': 'homepage', **_pending_counts(),
    })


@perm_required('content')
def home_section_edit(request, pk):
    section = get_object_or_404(HomeSection, pk=pk)
    form = HomeSectionForm(request.POST or None, request.FILES or None, instance=section)
    if request.method == 'POST':
        if request.POST.get('clear_image') and section.image:
            section.image = None
            section.save(update_fields=['image'])
            messages.info(request, 'تم حذف الصورة')
            return redirect('dash_home_edit', pk=section.pk)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم حفظ قسم «{section.label}»')
            return redirect('dash_home')
    return render(request, 'dashboard/homepage/form.html', {
        'form': form, 'section': section, 'active_page': 'homepage', **_pending_counts(),
    })


@perm_required('content')
@require_POST
def home_section_move(request, pk, direction):
    _swap(HomeSection, get_object_or_404(HomeSection, pk=pk), direction)
    return redirect('dash_home')


@perm_required('content')
@require_POST
def home_section_toggle(request, pk):
    section = get_object_or_404(HomeSection, pk=pk)
    section.is_active = not section.is_active
    section.save(update_fields=['is_active'])
    return redirect('dash_home')


@perm_required('content')
def nav_list(request):
    NavLink.ensure_defaults()
    return render(request, 'dashboard/navbar/list.html', {
        'links': NavLink.objects.select_related('category', 'policy'),
        'active_page': 'navbar', **_pending_counts(),
    })


@perm_required('content')
def nav_form(request, pk=None):
    link = get_object_or_404(NavLink, pk=pk) if pk else None
    form = NavLinkForm(request.POST or None, instance=link)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        if link is None:
            obj.ordering = (NavLink.objects.aggregate(m=Max('ordering'))['m'] or 0) + 1
        obj.save()
        messages.success(request, 'تم حفظ الرابط')
        return redirect('dash_nav')
    return render(request, 'dashboard/navbar/form.html', {
        'form': form, 'object': link, 'active_page': 'navbar', **_pending_counts(),
    })


@perm_required('content')
@require_POST
def nav_move(request, pk, direction):
    _swap(NavLink, get_object_or_404(NavLink, pk=pk), direction)
    return redirect('dash_nav')


@perm_required('content')
@require_POST
def nav_toggle(request, pk):
    link = get_object_or_404(NavLink, pk=pk)
    link.is_active = not link.is_active
    link.save(update_fields=['is_active'])
    return redirect('dash_nav')


@perm_required('content')
@require_POST
def nav_delete(request, pk):
    get_object_or_404(NavLink, pk=pk).delete()
    messages.info(request, 'تم حذف الرابط')
    return redirect('dash_nav')


@perm_required('content')
def policy_list(request):
    ensure_policy_defaults()
    return render(request, 'dashboard/policies/list.html', {
        'policies': Policy.objects.all(),
        'active_page': 'policies', **_pending_counts(),
    })


@perm_required('content')
def policy_form(request, pk=None):
    policy = get_object_or_404(Policy, pk=pk) if pk else None
    form = PolicyForm(request.POST or None, instance=policy)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ السياسة')
        return redirect('dash_policies')
    return render(request, 'dashboard/policies/form.html', {
        'form': form, 'object': Policy.objects.get(pk=policy.pk) if policy else None,
        'active_page': 'policies', **_pending_counts(),
    })


@perm_required('content')
@require_POST
def policy_delete(request, pk):
    get_object_or_404(Policy, pk=pk).delete()
    messages.info(request, 'تم حذف السياسة')
    return redirect('dash_policies')


# ===================================================================== staff
@perm_required('staff')
def staff_list(request):
    members = User.objects.filter(is_staff=True).select_related('staff_profile').order_by('-is_superuser', 'username')
    rows = []
    labels = dict(STAFF_PERMISSIONS)
    for member in members:
        perms = staff_permissions(member) if member.is_active else set()
        profile = getattr(member, 'staff_profile', None) if hasattr(member, 'staff_profile') else None
        rows.append({
            'user': member,
            'profile': profile,
            'labels': [labels[p] for p, _ in STAFF_PERMISSIONS if p in perms],
            'full': member.is_superuser or len(perms) == len(STAFF_PERMISSIONS),
        })
    return render(request, 'dashboard/staff/list.html', {
        'rows': rows, 'active_page': 'staff', **_pending_counts(),
    })


@perm_required('staff')
def staff_form(request, pk=None):
    member = get_object_or_404(User, pk=pk, is_staff=True) if pk else None
    if member is not None and member.is_superuser and not request.user.is_superuser:
        messages.error(request, 'المدير الأساسي بيتعدل من حسابه بس')
        return redirect('dash_staff')
    profile = None
    if member is not None:
        profile = StaffProfile.objects.filter(user=member).first()
    initial = {}
    if member is not None:
        initial = {
            'full_name': member.get_full_name(), 'username': member.username,
            'email': member.email, 'is_active': member.is_active,
            'job_title': profile.job_title if profile else '',
            'permissions': list(staff_permissions(member)),
        }
    form = StaffForm(request.POST or None, instance=member, initial=initial)
    editing_self = member is not None and member.pk == request.user.pk
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        with transaction.atomic():
            user = member or User(is_staff=True)
            first, _, last = data['full_name'].partition(' ')
            user.first_name, user.last_name = first[:150], last[:150]
            user.username = data['username']
            user.email = data['email']
            user.is_staff = True
            if not editing_self:
                user.is_active = data['is_active']
            if data['password']:
                user.set_password(data['password'])
            user.save()
            if not user.is_superuser:
                perms = list(data['permissions'])
                if editing_self and 'staff' not in perms:
                    perms.append('staff')  # never lock yourself out of this page
                StaffProfile.objects.update_or_create(
                    user=user, defaults={'permissions': perms, 'job_title': data['job_title']},
                )
            else:
                StaffProfile.objects.update_or_create(user=user, defaults={'job_title': data['job_title']})
        messages.success(request, 'تم حفظ الإداري')
        return redirect('dash_staff')
    return render(request, 'dashboard/staff/form.html', {
        'form': form, 'member': member, 'editing_self': editing_self,
        'is_owner': bool(member and member.is_superuser),
        'active_page': 'staff', **_pending_counts(),
    })


@perm_required('staff')
@require_POST
def staff_delete(request, pk):
    member = get_object_or_404(User, pk=pk, is_staff=True)
    if member.pk == request.user.pk or member.is_superuser:
        messages.error(request, 'مينفعش تحذف الحساب ده')
        return redirect('dash_staff')
    member.delete()
    messages.info(request, 'تم حذف الإداري')
    return redirect('dash_staff')
