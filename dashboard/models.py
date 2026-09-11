"""RGS TOWER — data models (single app architecture)."""

import random
import string
from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .i18n import pick

ZERO = Decimal('0.00')


def unique_slugify(instance, value, field_name='slug'):
    """Build a slug that is unique for the model of `instance`."""
    base = slugify(value, allow_unicode=True) or 'item'
    slug = base
    model = instance.__class__
    counter = 2
    while model.objects.filter(**{field_name: slug}).exclude(pk=instance.pk).exists():
        slug = f'{base}-{counter}'
        counter += 1
    return slug


# ============================================================== site settings
class SiteSettings(models.Model):
    """Singleton row holding everything the owner edits from the dashboard."""

    brand_name_ar = models.CharField(max_length=120, default='RGS TOWER')
    brand_name_en = models.CharField(max_length=120, default='RGS TOWER')
    tagline_ar = models.CharField(max_length=200, blank=True, default='أناقة الرجل الحقيقي')
    tagline_en = models.CharField(max_length=200, blank=True, default='Menswear, refined.')
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site/', blank=True, null=True)

    about_ar = models.TextField(blank=True, default='')
    about_en = models.TextField(blank=True, default='')

    # contact + social
    phone = models.CharField(max_length=40, blank=True, default='')
    whatsapp = models.CharField(max_length=40, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    address_ar = models.CharField(max_length=255, blank=True, default='')
    address_en = models.CharField(max_length=255, blank=True, default='')
    facebook_url = models.URLField(blank=True, default='')
    instagram_url = models.URLField(blank=True, default='')
    tiktok_url = models.URLField(blank=True, default='')
    youtube_url = models.URLField(blank=True, default='')

    # commerce
    currency_ar = models.CharField(max_length=20, default='ج.م')
    currency_en = models.CharField(max_length=20, default='EGP')
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('60.00'))
    free_shipping_threshold = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('2000.00'),
        help_text='0 = لا يوجد شحن مجاني / 0 disables free shipping',
    )
    low_stock_threshold = models.PositiveIntegerField(default=5)
    orders_enabled = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site settings'
        verbose_name_plural = 'Site settings'

    def __str__(self):
        return self.brand_name_en

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    # -- localized helpers
    @property
    def brand_name(self):
        return pick(self.brand_name_ar, self.brand_name_en)

    @property
    def tagline(self):
        return pick(self.tagline_ar, self.tagline_en)

    @property
    def about(self):
        return pick(self.about_ar, self.about_en)

    @property
    def address(self):
        return pick(self.address_ar, self.address_en)

    @property
    def currency(self):
        return pick(self.currency_ar, self.currency_en)

    def shipping_for(self, subtotal, governorate=None):
        """Flat fee, free above the threshold, optional per-governorate override."""
        fee = self.shipping_fee
        if governorate is not None and governorate.shipping_fee is not None:
            fee = governorate.shipping_fee
        threshold = self.free_shipping_threshold or ZERO
        if threshold > ZERO and Decimal(subtotal) >= threshold:
            return ZERO
        return fee


# ============================================================== announcements
class Announcement(models.Model):
    """Scrolling messages in the top bar."""

    text_ar = models.CharField(max_length=255)
    text_en = models.CharField(max_length=255, blank=True, default='')
    link = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordering', '-created_at']

    def __str__(self):
        return self.text_ar

    @property
    def text(self):
        return pick(self.text_ar, self.text_en)


# ======================================================================= hero
class Banner(models.Model):
    """Hero slides on the homepage."""

    title_ar = models.CharField(max_length=160, blank=True, default='')
    title_en = models.CharField(max_length=160, blank=True, default='')
    subtitle_ar = models.CharField(max_length=255, blank=True, default='')
    subtitle_en = models.CharField(max_length=255, blank=True, default='')
    button_text_ar = models.CharField(max_length=60, blank=True, default='')
    button_text_en = models.CharField(max_length=60, blank=True, default='')
    link = models.CharField(max_length=255, blank=True, default='')
    image = models.ImageField(upload_to='banners/')
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'id']

    def __str__(self):
        return self.title_ar or self.title_en or f'Banner #{self.pk}'

    @property
    def title(self):
        return pick(self.title_ar, self.title_en)

    @property
    def subtitle(self):
        return pick(self.subtitle_ar, self.subtitle_en)

    @property
    def button_text(self):
        return pick(self.button_text_ar, self.button_text_en)


# ================================================================= categories
class Category(models.Model):
    name_ar = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120, blank=True, default='')
    slug = models.SlugField(max_length=160, unique=True, blank=True, allow_unicode=True)
    description_ar = models.TextField(blank=True, default='')
    description_en = models.TextField(blank=True, default='')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordering', 'id']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name_ar or self.name_en

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name_en or self.name_ar)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop') + f'?category={self.slug}'

    @property
    def name(self):
        return pick(self.name_ar, self.name_en)

    @property
    def description(self):
        return pick(self.description_ar, self.description_en)

    @property
    def live_products_count(self):
        return self.products.filter(is_active=True).count()


# ====================================================================== sizes
class Size(models.Model):
    name = models.CharField(max_length=20, unique=True)
    name_ar = models.CharField(max_length=20, blank=True, default='')
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'id']

    def __str__(self):
        return self.name

    @property
    def label(self):
        return pick(self.name_ar or self.name, self.name)


# =================================================================== products
class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products'
    )
    name_ar = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True, default='')
    slug = models.SlugField(max_length=240, unique=True, blank=True, allow_unicode=True)
    sku = models.CharField(max_length=60, blank=True, default='')
    short_ar = models.CharField(max_length=255, blank=True, default='')
    short_en = models.CharField(max_length=255, blank=True, default='')
    description_ar = models.TextField(blank=True, default='')
    description_en = models.TextField(blank=True, default='')

    price = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    compare_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='السعر قبل الخصم (اختياري) / original price, optional',
    )

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_new = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordering', '-created_at']

    def __str__(self):
        return self.name_ar or self.name_en

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name_en or self.name_ar)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    # -- localized helpers
    @property
    def name(self):
        return pick(self.name_ar, self.name_en)

    @property
    def short(self):
        return pick(self.short_ar, self.short_en)

    @property
    def description(self):
        return pick(self.description_ar, self.description_en)

    # -- media
    @property
    def main_image(self):
        img = self.images.filter(is_main=True).first() or self.images.first()
        return img.image if img else None

    @property
    def hover_image(self):
        imgs = list(self.images.all()[:2])
        return imgs[1].image if len(imgs) > 1 else None

    # -- stock
    @property
    def total_stock(self):
        return self.variants.aggregate(t=models.Sum('quantity'))['t'] or 0

    @property
    def in_stock(self):
        return self.total_stock > 0

    # -- pricing
    @property
    def active_promotion(self):
        """Best running promotion that applies to this product (cached per instance)."""
        if not hasattr(self, '_promo_cache'):
            best, best_amount = None, ZERO
            for promo in Promotion.running():
                if not promo.applies_to(self):
                    continue
                amount = promo.amount_for(self.price)
                if amount > best_amount:
                    best, best_amount = promo, amount
            self._promo_cache = best
        return self._promo_cache

    @property
    def final_price(self):
        promo = self.active_promotion
        if promo:
            return max(ZERO, (self.price - promo.amount_for(self.price)).quantize(Decimal('0.01')))
        return self.price

    @property
    def has_discount(self):
        return self.final_price < self.price or bool(
            self.compare_price and self.compare_price > self.price
        )

    @property
    def old_price(self):
        if self.final_price < self.price:
            return self.price
        if self.compare_price and self.compare_price > self.price:
            return self.compare_price
        return None

    @property
    def discount_percent(self):
        old = self.old_price
        if not old or old <= ZERO:
            return 0
        return int(round((old - self.final_price) / old * 100))

    # -- options
    @property
    def available_sizes(self):
        ids = self.variants.filter(quantity__gt=0).values_list('size_id', flat=True)
        return Size.objects.filter(id__in=[i for i in ids if i])


class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='colors')
    name_ar = models.CharField(max_length=60)
    name_en = models.CharField(max_length=60, blank=True, default='')
    hex_code = models.CharField(max_length=9, default='#000000')
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'id']

    def __str__(self):
        return f'{self.product} — {self.name_ar}'

    @property
    def name(self):
        return pick(self.name_ar, self.name_en)

    @property
    def main_image(self):
        img = self.images.first()
        return img.image if img else None

    @property
    def stock(self):
        return self.variants.aggregate(t=models.Sum('quantity'))['t'] or 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    color = models.ForeignKey(
        ProductColor, on_delete=models.CASCADE, null=True, blank=True, related_name='images'
    )
    image = models.ImageField(upload_to='products/')
    is_main = models.BooleanField(default=False)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-is_main', 'ordering', 'id']

    def __str__(self):
        return f'Image #{self.pk} — {self.product}'


class ProductVariant(models.Model):
    """One sellable combination: product + color + size, with its own quantity."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.ForeignKey(
        ProductColor, on_delete=models.CASCADE, null=True, blank=True, related_name='variants'
    )
    size = models.ForeignKey(
        Size, on_delete=models.CASCADE, null=True, blank=True, related_name='variants'
    )
    quantity = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=60, blank=True, default='')

    class Meta:
        ordering = ['color__ordering', 'size__ordering', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'color', 'size'], name='uniq_product_color_size'
            )
        ]

    def __str__(self):
        return f'{self.product} / {self.color_label} / {self.size_label}'

    @property
    def color_label(self):
        return self.color.name if self.color else '—'

    @property
    def size_label(self):
        return self.size.label if self.size else '—'

    @property
    def image(self):
        if self.color:
            img = self.color.images.first()
            if img:
                return img.image
        return self.product.main_image


# ================================================================= promotions
DISCOUNT_TYPES = [
    ('percent', 'نسبة مئوية / Percent'),
    ('fixed', 'مبلغ ثابت / Fixed amount'),
]


class Promotion(models.Model):
    """Automatic discounts: everything, a set of categories, or specific products."""

    SCOPES = [
        ('all', 'كل المنتجات / All products'),
        ('category', 'كاتيجوري معينة / Selected categories'),
        ('product', 'منتجات معينة / Selected products'),
    ]

    title = models.CharField(max_length=140)
    scope = models.CharField(max_length=12, choices=SCOPES, default='all')
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES, default='percent')
    value = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    categories = models.ManyToManyField(Category, blank=True, related_name='promotions')
    products = models.ManyToManyField(Product, blank=True, related_name='promotions')
    badge_ar = models.CharField(max_length=40, blank=True, default='')
    badge_en = models.CharField(max_length=40, blank=True, default='')
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @classmethod
    def running(cls):
        now = timezone.now()
        return cls.objects.filter(is_active=True).filter(
            models.Q(start_at__isnull=True) | models.Q(start_at__lte=now)
        ).filter(
            models.Q(end_at__isnull=True) | models.Q(end_at__gte=now)
        ).prefetch_related('categories', 'products')

    @property
    def is_running(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_at and self.start_at > now:
            return False
        if self.end_at and self.end_at < now:
            return False
        return True

    @property
    def badge(self):
        return pick(self.badge_ar, self.badge_en)

    def applies_to(self, product):
        if self.scope == 'all':
            return True
        if self.scope == 'category':
            return product.category_id in {c.id for c in self.categories.all()}
        return product.id in {p.id for p in self.products.all()}

    def amount_for(self, price):
        price = Decimal(price or 0)
        if self.discount_type == 'percent':
            return (price * self.value / Decimal('100')).quantize(Decimal('0.01'))
        return min(price, Decimal(self.value)).quantize(Decimal('0.01'))


class Coupon(models.Model):
    """Promo code the customer types at checkout."""

    code = models.CharField(max_length=40, unique=True)
    description = models.CharField(max_length=200, blank=True, default='')
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES, default='percent')
    value = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    min_order = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    free_shipping = models.BooleanField(default=False)
    max_uses = models.PositiveIntegerField(default=0, help_text='0 = غير محدود / 0 = unlimited')
    used_count = models.PositiveIntegerField(default=0)
    categories = models.ManyToManyField(Category, blank=True, related_name='coupons')
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = (self.code or '').strip().upper()
        super().save(*args, **kwargs)

    @property
    def is_running(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_at and self.start_at > now:
            return False
        if self.end_at and self.end_at < now:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True

    def validate_for(self, subtotal):
        """Return (ok, error_key)."""
        now = timezone.now()
        if not self.is_active:
            return False, 'coupon_inactive'
        if self.start_at and self.start_at > now:
            return False, 'coupon_not_started'
        if self.end_at and self.end_at < now:
            return False, 'coupon_expired'
        if self.max_uses and self.used_count >= self.max_uses:
            return False, 'coupon_used_up'
        if self.min_order and Decimal(subtotal) < self.min_order:
            return False, 'coupon_min_order'
        return True, ''

    def amount_for(self, subtotal):
        subtotal = Decimal(subtotal or 0)
        if self.discount_type == 'percent':
            return (subtotal * self.value / Decimal('100')).quantize(Decimal('0.01'))
        return min(subtotal, Decimal(self.value)).quantize(Decimal('0.01'))


# ===================================================================== orders
class Governorate(models.Model):
    name_ar = models.CharField(max_length=80)
    name_en = models.CharField(max_length=80, blank=True, default='')
    shipping_fee = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='اتركه فارغًا لاستخدام سعر الشحن العام / blank = default fee',
    )
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_ar']

    def __str__(self):
        return self.name_ar or self.name_en

    @property
    def name(self):
        return pick(self.name_ar, self.name_en)


class Order(models.Model):
    STATUSES = [
        ('pending', 'قيد المراجعة / Pending'),
        ('confirmed', 'تم التأكيد / Confirmed'),
        ('shipped', 'تم الشحن / Shipped'),
        ('delivered', 'تم التسليم / Delivered'),
        ('cancelled', 'ملغي / Cancelled'),
    ]

    order_number = models.CharField(max_length=20, unique=True, blank=True)
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    phone_alt = models.CharField(max_length=30, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    governorate = models.ForeignKey(
        Governorate, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders'
    )
    city = models.CharField(max_length=120, blank=True, default='')
    address = models.TextField()
    notes = models.TextField(blank=True, default='')

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    discount_total = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    coupon = models.ForeignKey(
        Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders'
    )
    coupon_code = models.CharField(max_length=40, blank=True, default='')
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)

    status = models.CharField(max_length=12, choices=STATUSES, default='pending')
    admin_note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_number():
        while True:
            code = 'RGS' + ''.join(random.choices(string.digits, k=7))
            if not Order.objects.filter(order_number=code).exists():
                return code

    @property
    def items_count(self):
        return self.items.aggregate(t=models.Sum('quantity'))['t'] or 0

    @property
    def status_label(self):
        return dict(self.STATUSES).get(self.status, self.status)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items'
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items'
    )
    product_name = models.CharField(max_length=200)
    color_name = models.CharField(max_length=60, blank=True, default='')
    size_name = models.CharField(max_length=40, blank=True, default='')
    image_url = models.CharField(max_length=300, blank=True, default='')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    quantity = models.PositiveIntegerField(default=1)
    line_total = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)

    def __str__(self):
        return f'{self.product_name} x{self.quantity}'


# =================================================================== messages
class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=30, blank=True, default='')
    subject = models.CharField(max_length=160, blank=True, default='')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.subject or "رسالة"}'
