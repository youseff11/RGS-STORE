"""Admin dashboard views — RGS TOWER."""

from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, F, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    AnnouncementForm, BannerForm, CategoryForm, ColorForm, CouponForm,
    GovernorateForm, ProductForm, PromotionForm, SiteSettingsForm, SizeForm,
)
from .models import (
    Announcement, Banner, Category, ContactMessage, Coupon, Governorate, Order,
    Product, ProductColor, ProductImage, ProductVariant, Promotion,
    SiteSettings, Size,
)

staff_required = user_passes_test(
    lambda u: u.is_authenticated and u.is_active and u.is_staff,
    login_url='/dashboard/login/',
)

PAGE_SIZE = 20


def _paginate(request, queryset, size=PAGE_SIZE):
    return Paginator(queryset, size).get_page(request.GET.get('page'))


def _pending_counts():
    return {
        'new_orders': Order.objects.filter(status='pending').count(),
        'unread_messages': ContactMessage.objects.filter(is_read=False).count(),
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

    site = SiteSettings.load()
    low_stock = (
        Product.objects.annotate(stock=Sum('variants__quantity'))
        .filter(is_active=True)
        .filter(Q(stock__lte=site.low_stock_threshold) | Q(stock__isnull=True))
        .order_by('stock')[:8]
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

    context = {
        'stats': {
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
        'recent_orders': orders.select_related('governorate')[:8],
        'low_stock': low_stock,
        'top_products': top_products,
        'chart': chart,
        'active_page': 'index',
        **_pending_counts(),
    }
    return render(request, 'dashboard/index.html', context)


# ================================================================== products
@staff_required
def product_list(request):
    query = (request.GET.get('q') or '').strip()
    category = request.GET.get('category') or ''
    status = request.GET.get('status') or ''

    products = (
        Product.objects.select_related('category')
        .prefetch_related('images')
        .annotate(stock=Sum('variants__quantity'))
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
    elif status == 'out':
        products = products.filter(Q(stock__isnull=True) | Q(stock=0))

    context = {
        'page_obj': _paginate(request, products),
        'categories': Category.objects.all(),
        'q': query, 'category': category, 'status': status,
        'active_page': 'products',
        **_pending_counts(),
    }
    return render(request, 'dashboard/products/list.html', context)


@staff_required
def product_form(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else None
    form = ProductForm(request.POST or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        obj = form.save()
        messages.success(request, 'تم حفظ المنتج بنجاح')
        if 'save_and_media' in request.POST or product is None:
            return redirect('dash_product_media', pk=obj.pk)
        return redirect('dash_products')
    context = {
        'form': form,
        'product': product,
        'active_page': 'products',
        **_pending_counts(),
    }
    return render(request, 'dashboard/products/form.html', context)


@staff_required
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


@staff_required
def product_stock(request, pk):
    """Colors x sizes quantity matrix."""
    product = get_object_or_404(Product, pk=pk)
    colors = list(product.colors.all())
    sizes = list(Size.objects.all())

    if request.method == 'POST':
        chosen_sizes = request.POST.getlist('sizes')
        chosen_ids = [int(s) for s in chosen_sizes if s.isdigit()]
        kept = set()
        for color in (colors or [None]):
            for size in (sizes or [None]):
                if size is not None and size.id not in chosen_ids:
                    continue
                key = f'q_{color.id if color else 0}_{size.id if size else 0}'
                raw = (request.POST.get(key) or '').strip()
                if raw == '':
                    continue
                try:
                    qty = max(0, int(raw))
                except ValueError:
                    continue
                variant, _ = ProductVariant.objects.update_or_create(
                    product=product, color=color, size=size,
                    defaults={'quantity': qty},
                )
                kept.add(variant.pk)
        product.variants.exclude(pk__in=kept).delete()
        messages.success(request, 'تم تحديث المخزون')
        return redirect('dash_product_stock', pk=product.pk)

    existing = {}
    active_size_ids = set()
    for variant in product.variants.all():
        existing[f'{variant.color_id or 0}-{variant.size_id or 0}'] = variant.quantity
        if variant.size_id:
            active_size_ids.add(variant.size_id)
    if not active_size_ids:
        active_size_ids = {s.id for s in sizes}

    grid = []
    for color in (colors or [None]):
        cells = []
        for size in (sizes or [None]):
            cells.append({
                'size': size,
                'key': f'q_{color.id if color else 0}_{size.id if size else 0}',
                'value': existing.get(f'{color.id if color else 0}-{size.id if size else 0}', ''),
            })
        grid.append({'color': color, 'cells': cells})

    context = {
        'product': product,
        'sizes': sizes,
        'grid': grid,
        'active_size_ids': active_size_ids,
        'active_page': 'products',
        **_pending_counts(),
    }
    return render(request, 'dashboard/products/stock.html', context)


@staff_required
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, 'تم حذف المنتج')
    return redirect('dash_products')


@staff_required
def product_toggle(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save(update_fields=['is_active'])
    return redirect(request.META.get('HTTP_REFERER', 'dash_products'))


@staff_required
@require_POST
def color_delete(request, pk):
    color = get_object_or_404(ProductColor, pk=pk)
    product_id = color.product_id
    color.delete()
    messages.info(request, 'تم حذف اللون')
    return redirect('dash_product_media', pk=product_id)


@staff_required
@require_POST
def image_delete(request, pk):
    image = get_object_or_404(ProductImage, pk=pk)
    product_id = image.product_id
    image.delete()
    messages.info(request, 'تم حذف الصورة')
    return redirect('dash_product_media', pk=product_id)


@staff_required
def image_main(request, pk):
    image = get_object_or_404(ProductImage, pk=pk)
    ProductImage.objects.filter(product=image.product).update(is_main=False)
    ProductImage.objects.filter(pk=image.pk).update(is_main=True)
    return redirect('dash_product_media', pk=image.product_id)


# ================================================================ categories
@staff_required
def category_list(request):
    categories = Category.objects.annotate(count=Count('products'))
    return render(request, 'dashboard/categories/list.html', {
        'categories': categories, 'active_page': 'categories', **_pending_counts(),
    })


@staff_required
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


@staff_required
@require_POST
def category_delete(request, pk):
    get_object_or_404(Category, pk=pk).delete()
    messages.info(request, 'تم حذف القسم')
    return redirect('dash_categories')


# ===================================================================== sizes
@staff_required
def size_list(request):
    form = SizeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'تمت إضافة المقاس')
        return redirect('dash_sizes')
    return render(request, 'dashboard/sizes/list.html', {
        'sizes': Size.objects.all(), 'form': form,
        'active_page': 'sizes', **_pending_counts(),
    })


@staff_required
@require_POST
def size_delete(request, pk):
    get_object_or_404(Size, pk=pk).delete()
    messages.info(request, 'تم حذف المقاس')
    return redirect('dash_sizes')


# ==================================================================== orders
@staff_required
def order_list(request):
    query = (request.GET.get('q') or '').strip()
    status = request.GET.get('status') or ''
    orders = Order.objects.select_related('governorate').prefetch_related('items')
    if query:
        orders = orders.filter(
            Q(order_number__icontains=query) | Q(full_name__icontains=query)
            | Q(phone__icontains=query)
        )
    if status:
        orders = orders.filter(status=status)
    return render(request, 'dashboard/orders/list.html', {
        'page_obj': _paginate(request, orders),
        'q': query, 'status': status,
        'statuses': Order.STATUSES,
        'active_page': 'orders', **_pending_counts(),
    })


@staff_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('governorate', 'coupon').prefetch_related('items'), pk=pk
    )
    if request.method == 'POST':
        order.admin_note = request.POST.get('admin_note') or ''
        order.save(update_fields=['admin_note'])
        messages.success(request, 'تم حفظ الملاحظة')
        return redirect('dash_order_detail', pk=order.pk)
    return render(request, 'dashboard/orders/detail.html', {
        'order': order, 'statuses': Order.STATUSES,
        'active_page': 'orders', **_pending_counts(),
    })


@staff_required
@require_POST
def order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    status = request.POST.get('status')
    if status in dict(Order.STATUSES):
        order.status = status
        order.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'تم تحديث حالة الطلب')
    return redirect(request.META.get('HTTP_REFERER') or 'dash_orders')


@staff_required
@require_POST
def order_delete(request, pk):
    get_object_or_404(Order, pk=pk).delete()
    messages.info(request, 'تم حذف الطلب')
    return redirect('dash_orders')


@staff_required
def order_print(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('governorate').prefetch_related('items'), pk=pk
    )
    return render(request, 'dashboard/orders/print.html', {'order': order})


# =================================================================== coupons
@staff_required
def coupon_list(request):
    return render(request, 'dashboard/coupons/list.html', {
        'coupons': Coupon.objects.all(), 'active_page': 'coupons', **_pending_counts(),
    })


@staff_required
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


@staff_required
@require_POST
def coupon_delete(request, pk):
    get_object_or_404(Coupon, pk=pk).delete()
    messages.info(request, 'تم حذف الكود')
    return redirect('dash_coupons')


# ================================================================ promotions
@staff_required
def promotion_list(request):
    return render(request, 'dashboard/promotions/list.html', {
        'promotions': Promotion.objects.prefetch_related('categories', 'products'),
        'active_page': 'promotions', **_pending_counts(),
    })


@staff_required
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


@staff_required
@require_POST
def promotion_delete(request, pk):
    get_object_or_404(Promotion, pk=pk).delete()
    messages.info(request, 'تم حذف العرض')
    return redirect('dash_promotions')


# ============================================================= announcements
@staff_required
def announcement_list(request):
    return render(request, 'dashboard/announcements/list.html', {
        'announcements': Announcement.objects.all(),
        'active_page': 'announcements', **_pending_counts(),
    })


@staff_required
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


@staff_required
@require_POST
def announcement_delete(request, pk):
    get_object_or_404(Announcement, pk=pk).delete()
    messages.info(request, 'تم حذف الإعلان')
    return redirect('dash_announcements')


# =================================================================== banners
@staff_required
def banner_list(request):
    return render(request, 'dashboard/banners/list.html', {
        'banners': Banner.objects.all(), 'active_page': 'banners', **_pending_counts(),
    })


@staff_required
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


@staff_required
@require_POST
def banner_delete(request, pk):
    get_object_or_404(Banner, pk=pk).delete()
    messages.info(request, 'تم حذف البانر')
    return redirect('dash_banners')


# ============================================================== governorates
@staff_required
def governorate_list(request):
    return render(request, 'dashboard/governorates/list.html', {
        'governorates': Governorate.objects.all(),
        'active_page': 'governorates', **_pending_counts(),
    })


@staff_required
def governorate_form(request, pk=None):
    obj = get_object_or_404(Governorate, pk=pk) if pk else None
    form = GovernorateForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'تم الحفظ')
        return redirect('dash_governorates')
    return render(request, 'dashboard/governorates/form.html', {
        'form': form, 'object': obj, 'active_page': 'governorates', **_pending_counts(),
    })


@staff_required
@require_POST
def governorate_delete(request, pk):
    get_object_or_404(Governorate, pk=pk).delete()
    messages.info(request, 'تم الحذف')
    return redirect('dash_governorates')


# ================================================================== messages
@staff_required
def message_list(request):
    return render(request, 'dashboard/messages/list.html', {
        'items': _paginate(request, ContactMessage.objects.all()),
        'active_page': 'messages', **_pending_counts(),
    })


@staff_required
def message_detail(request, pk):
    item = get_object_or_404(ContactMessage, pk=pk)
    if not item.is_read:
        item.is_read = True
        item.save(update_fields=['is_read'])
    return render(request, 'dashboard/messages/detail.html', {
        'item': item, 'active_page': 'messages', **_pending_counts(),
    })


@staff_required
@require_POST
def message_delete(request, pk):
    get_object_or_404(ContactMessage, pk=pk).delete()
    messages.info(request, 'تم حذف الرسالة')
    return redirect('dash_messages')


# ================================================================== settings
@staff_required
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
