"""RGS TOWER — data models (single app architecture)."""

import random
import re
import string
import uuid
from decimal import ROUND_UP, Decimal

from django.conf import settings
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
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
    orders_enabled = models.BooleanField(default=True)

    # payments
    cod_enabled = models.BooleanField(default=True)
    paypal_enabled = models.BooleanField(default=False)
    paypal_link = models.URLField(
        blank=True, default='',
        help_text='لينك الدفع — مثال: https://paypal.me/YourName',
    )
    paypal_client_id = models.CharField(max_length=255, blank=True, default='')
    paypal_secret = models.CharField(max_length=255, blank=True, default='')
    paypal_sandbox = models.BooleanField(default=False)
    paypal_currency = models.CharField(max_length=3, default='USD')
    paypal_rate = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal('50.0000'),
        help_text='كام جنيه = 1 دولار',
    )

    # ---- Google sign-in (OAuth 2.0 / OpenID Connect) ----
    google_login_enabled = models.BooleanField(default=False)
    google_button_icon = models.FileField(
        upload_to='site/', blank=True, null=True,
        validators=[FileExtensionValidator(['png', 'svg', 'webp', 'jpg', 'jpeg'])],
    )
    google_client_id = models.CharField(
        max_length=255, blank=True, default='',
        help_text='من Google Cloud Console — بينتهي بـ .apps.googleusercontent.com',
    )
    google_client_secret = models.CharField(
        max_length=255, blank=True, default='',
        help_text='الـ Client secret من نفس الشاشة — بيتحفظ عندنا ومش بيظهر تاني',
    )

    # ---- Discord sign-in (OAuth 2.0) ----
    discord_login_enabled = models.BooleanField(default=False)
    discord_button_icon = models.FileField(
        upload_to='site/', blank=True, null=True,
        validators=[FileExtensionValidator(['png', 'svg', 'webp', 'jpg', 'jpeg'])],
    )
    discord_client_id = models.CharField(
        max_length=64, blank=True, default='',
        help_text='من Discord Developer Portal ← OAuth2 — رقم طويل',
    )
    discord_client_secret = models.CharField(
        max_length=255, blank=True, default='',
        help_text='الـ Client secret من نفس الشاشة — بيتحفظ عندنا ومش بيظهر تاني',
    )

    # reviews + sharing
    reviews_auto_publish = models.BooleanField(default=True)
    share_image = models.ImageField(upload_to='site/', blank=True, null=True)

    # ---- email notifications (Gmail or any SMTP) ----
    emails_enabled = models.BooleanField(default=False)
    notify_email = models.EmailField(
        blank=True, default='', help_text='الإيميل اللي هتوصلك عليه الإشعارات',
    )
    notify_new_order = models.BooleanField(default=True)
    notify_new_ticket = models.BooleanField(default=True)
    notify_new_message = models.BooleanField(default=True)
    notify_new_review = models.BooleanField(default=True)
    notify_customer_order = models.BooleanField(default=True)
    notify_customer_ticket = models.BooleanField(default=True)
    site_url = models.CharField(
        max_length=200, blank=True, default='',
        help_text='لينك المتجر — بيتحط في الإيميلات، مثال: https://rgstower.com',
    )
    smtp_host = models.CharField(max_length=120, blank=True, default='smtp.gmail.com')
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_user = models.CharField(
        max_length=200, blank=True, default='', help_text='الجيميل اللي هيبعت منه',
    )
    smtp_password = models.CharField(
        max_length=200, blank=True, default='',
        help_text='App password من جوجل (16 حرف) — مش باسورد الإيميل العادي',
    )
    smtp_use_tls = models.BooleanField(default=True)

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

    @property
    def mail_ready(self):
        """True when the store can actually send an email."""
        return bool(
            self.emails_enabled and self.smtp_host and self.smtp_user and self.smtp_password
        )

    @property
    def mail_from(self):
        return f'{self.brand_name_en or "RGS TOWER"} <{self.smtp_user}>' if self.smtp_user else ''

    def absolute_url(self, path=''):
        base = (self.site_url or '').strip().rstrip('/')
        path = path or ''
        if not base:
            return path
        return base + path if path.startswith('/') else f'{base}/{path}'

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

    # -- sign in with Google
    @property
    def google_ready(self):
        """The «Continue with Google» button only shows with both keys saved."""
        return bool(
            self.google_login_enabled and self.google_client_id and self.google_client_secret
        )

    # -- sign in with Discord
    @property
    def discord_ready(self):
        """The «Continue with Discord» button only shows with both keys saved."""
        return bool(
            self.discord_login_enabled and self.discord_client_id and self.discord_client_secret
        )

    @property
    def social_login_ready(self):
        return self.google_ready or self.discord_ready

    # -- payments
    @property
    def paypal_smart_ready(self):
        """Official PayPal button (auto-confirmed) needs both API keys."""
        return bool(self.paypal_enabled and self.paypal_client_id and self.paypal_secret)

    @property
    def paypal_ready(self):
        return bool(self.paypal_enabled and (self.paypal_link or self.paypal_smart_ready))

    @property
    def payment_methods(self):
        methods = []
        if self.paypal_ready:
            methods.append('paypal')
        if self.cod_enabled:
            methods.append('cod')
        return methods

    def to_paypal_amount(self, amount_egp):
        rate = self.paypal_rate or Decimal('1')
        if rate <= ZERO:
            rate = Decimal('1')
        return (Decimal(amount_egp or 0) / rate).quantize(Decimal('0.01'), rounding=ROUND_UP)

    def free_threshold_for(self, country=None):
        """Free-shipping threshold for a country (its own value, else the general one). 0 = never free."""
        if country is not None and country.free_shipping_over is not None:
            return country.free_shipping_over
        return self.free_shipping_threshold or ZERO

    def shipping_for(self, subtotal, country=None):
        """Flat fee, free above the threshold — each country can override both."""
        fee = self.shipping_fee
        if country is not None and country.shipping_fee is not None:
            fee = country.shipping_fee
        threshold = self.free_threshold_for(country)
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


# =================================================================== services
class Service(models.Model):
    """A graphic service the customer picks on a design (it replaced clothing sizes).

    Malak writes the services himself from the dashboard. Each one can add an
    extra price on top of the design's price, and services have no stock —
    a design is orderable in every colour × service that's switched on for it.
    """

    name_ar = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120, blank=True, default='')
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=ZERO,
        help_text='بيتزوّد على سعر الديزاين — 0 = من غير زيادة',
    )
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'id']

    def __str__(self):
        return self.name_ar or self.name_en

    @property
    def name(self):
        return pick(self.name_ar, self.name_en)

    label = name

    @property
    def products_count(self):
        return self.variants.values('product').distinct().count()


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

    # -- availability (services have no stock)
    def live_variants(self):
        """Variants the customer can order: no service, or a service that's switched on."""
        return self.variants.filter(models.Q(service__isnull=True) | models.Q(service__is_active=True))

    @property
    def in_stock(self):
        return self.live_variants().exists()

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

    # -- services
    @property
    def selected_service_ids(self):
        return set(self.variants.exclude(service=None).values_list('service_id', flat=True))

    @property
    def available_services(self):
        return Service.objects.filter(
            is_active=True, variants__product=self,
        ).distinct().order_by('ordering', 'id')

    @property
    def price_from(self):
        """Lowest price a customer can pay for this design (design + cheapest service)."""
        extras = [s.price for s in self.available_services]
        return self.final_price + (min(extras) if extras else ZERO)

    @property
    def old_price_from(self):
        """The crossed-out price that goes with `price_from`."""
        old = self.old_price
        return old + (self.price_from - self.final_price) if old else None

    @property
    def has_price_range(self):
        extras = {s.price for s in self.available_services}
        return len(extras) > 1

    def sync_variants(self, service_ids=None):
        """Keep exactly one variant per colour × chosen service.

        `service_ids=None` keeps the services already chosen for this design.
        No chosen services → one variant per colour (the design is still orderable).
        """
        if service_ids is None:
            service_ids = self.selected_service_ids
        services = list(Service.objects.filter(id__in=service_ids)) or [None]
        colors = list(self.colors.all()) or [None]
        existing = {}
        for variant in self.variants.all():
            existing.setdefault((variant.color_id, variant.service_id), variant)
        keep = set()
        for color in colors:
            for service in services:
                key = (color.id if color else None, service.id if service else None)
                variant = existing.get(key)
                if variant is None:
                    variant = ProductVariant.objects.create(product=self, color=color, service=service)
                keep.add(variant.pk)
        self.variants.exclude(pk__in=keep).delete()


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
    """One orderable combination: design + colour + service (no stock — always available)."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.ForeignKey(
        ProductColor, on_delete=models.CASCADE, null=True, blank=True, related_name='variants'
    )
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, null=True, blank=True, related_name='variants'
    )
    sku = models.CharField(max_length=60, blank=True, default='')

    class Meta:
        ordering = ['color__ordering', 'service__ordering', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'color', 'service'], name='uniq_product_color_service'
            )
        ]

    def __str__(self):
        return f'{self.product} / {self.color_label} / {self.service_label}'

    @property
    def color_label(self):
        return self.color.name if self.color else '—'

    @property
    def service_label(self):
        return self.service.name if self.service else '—'

    @property
    def is_available(self):
        return self.product.is_active and (self.service is None or self.service.is_active)

    @property
    def unit_price(self):
        """Design price (after any running offer) + the service's extra price."""
        extra = self.service.price if self.service else ZERO
        return self.product.final_price + extra

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
class Country(models.Model):
    """A country the store ships to — managed from «الدول والشحن» in the dashboard.

    (It used to be `Governorate` — Egyptian governorates — until the store started
    exporting; migration 0004 renamed it and loaded the list of countries.)
    """

    code = models.CharField(
        max_length=2, blank=True, default='', db_index=True,
        help_text='ISO code, e.g. EG, SA, AE',
    )
    name_ar = models.CharField(max_length=80)
    name_en = models.CharField(max_length=80, blank=True, default='')
    shipping_fee = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='اتركه فارغًا لاستخدام سعر الشحن العام / blank = default fee',
    )
    free_shipping_over = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='فارغ = حد الشحن المجاني العام · 0 = مفيش شحن مجاني للدولة دي',
    )
    delivery_ar = models.CharField(max_length=80, blank=True, default='')
    delivery_en = models.CharField(max_length=80, blank=True, default='')
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['ordering', 'name_ar']
        verbose_name = 'دولة'
        verbose_name_plural = 'الدول'

    def __str__(self):
        return self.name_ar or self.name_en

    @property
    def name(self):
        return pick(self.name_ar, self.name_en)

    @property
    def delivery(self):
        return pick(self.delivery_ar, self.delivery_en)


PAYMENT_METHODS = [
    ('paypal', 'PayPal'),
    ('cod', 'الدفع عند الاستلام'),
]
PAYMENT_METHOD_LABELS = {
    'paypal': ('PayPal', 'PayPal'),
    'cod': ('الدفع عند الاستلام', 'Cash on delivery'),
}
PAYMENT_STATUSES = [
    ('unpaid', 'لم يتم الدفع'),
    ('pending', 'بانتظار تأكيد الدفع'),
    ('paid', 'مدفوع'),
    ('failed', 'فشل الدفع'),
    ('refunded', 'مسترد'),
]
PAYMENT_STATUS_LABELS = {
    'unpaid': ('لم يتم الدفع', 'Unpaid'),
    'pending': ('بانتظار تأكيد الدفع', 'Awaiting confirmation'),
    'paid': ('مدفوع', 'Paid'),
    'failed': ('فشل الدفع', 'Payment failed'),
    'refunded': ('مسترد', 'Refunded'),
}
ORDER_STATUS_LABELS = {
    'pending': ('تم استلام طلبك', 'Order received'),
    'confirmed': ('جاري العمل', 'In progress'),
    'delivered': ('تم التسليم', 'Delivered'),
    'cancelled': ('ملغي', 'Cancelled'),
}


class Order(models.Model):
    STATUSES = [
        ('pending', 'تم استلام طلبك / Order received'),
        ('confirmed', 'جاري العمل / In progress'),
        ('delivered', 'تم التسليم / Delivered'),
        ('cancelled', 'ملغي / Cancelled'),
    ]

    order_number = models.CharField(max_length=20, unique=True, blank=True)
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    phone_alt = models.CharField(max_length=30, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders'
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

    # customer account + payment
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders',
    )
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='cod')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUSES, default='unpaid')
    paid_at = models.DateTimeField(null=True, blank=True)
    pay_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='المبلغ بعملة PayPal (دولار)',
    )
    pay_currency = models.CharField(max_length=3, blank=True, default='')
    paypal_order_id = models.CharField(max_length=64, blank=True, default='')
    paypal_capture_id = models.CharField(max_length=64, blank=True, default='')
    payer_email = models.CharField(max_length=254, blank=True, default='')
    payment_reference = models.CharField(
        max_length=120, blank=True, default='',
        help_text='رقم العملية اللي كتبه العميل بعد الدفع باللينك',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number

    @property
    def is_paid(self):
        return self.payment_status == 'paid'

    @property
    def payment_status_label(self):
        return pick(*PAYMENT_STATUS_LABELS.get(self.payment_status, (self.payment_status,) * 2))

    @property
    def payment_method_label(self):
        return pick(*PAYMENT_METHOD_LABELS.get(self.payment_method, (self.payment_method,) * 2))

    @property
    def status_label_local(self):
        return pick(*ORDER_STATUS_LABELS.get(self.status, (self.status,) * 2))

    @property
    def awaiting_payment(self):
        """PayPal order that the customer still has to pay."""
        return (
            self.payment_method == 'paypal'
            and self.payment_status in ('unpaid', 'failed')
            and self.status != 'cancelled'
        )

    def mark_paid(self, save=True):
        self.payment_status = 'paid'
        if not self.paid_at:
            self.paid_at = timezone.now()
        # بعد الدفع الطلب بيفضل «تم استلام طلبك» لحد ما الأدمن يحوّله «جاري العمل»
        if save:
            self.save(update_fields=['payment_status', 'paid_at', 'updated_at'])

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
    service_name = models.CharField(max_length=160, blank=True, default='')
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


# ================================================================== customers
class CustomerProfile(models.Model):
    """Extra data for a shopper account (auth.User with is_staff=False)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer'
    )
    phone = models.CharField(max_length=30, blank=True, default='')
    phone_alt = models.CharField(max_length=30, blank=True, default='')
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True, related_name='customers'
    )
    city = models.CharField(max_length=120, blank=True, default='')
    address = models.TextField(blank=True, default='')
    admin_note = models.TextField(blank=True, default='')
    # picture the customer uploads from «بياناتي» — wins over the Google / Discord one
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    # Google sign-in: `sub` never changes, even when the customer renames their
    # Gmail address, so it — not the email — is what identifies the account.
    google_id = models.CharField(max_length=64, blank=True, default='', db_index=True)
    google_picture = models.URLField(max_length=500, blank=True, default='')
    # Discord sign-in: the numeric user id, for the same reason
    discord_id = models.CharField(max_length=32, blank=True, default='', db_index=True)
    discord_avatar = models.URLField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.full_name or self.user.get_username()

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.first_name or ''

    @property
    def uses_google(self):
        return bool(self.google_id)

    @property
    def uses_discord(self):
        return bool(self.discord_id)

    @property
    def photo_url(self):
        """The customer's picture: uploaded one → Google → Discord → '' (initial letter is shown)."""
        if self.avatar:
            try:
                return self.avatar.url
            except ValueError:
                pass
        return self.google_picture or self.discord_avatar or ''

    @property
    def social_providers(self):
        """Names of the social accounts this customer signs in with (for messages)."""
        names = []
        if self.google_id:
            names.append('google')
        if self.discord_id:
            names.append('discord')
        return names

    @classmethod
    def for_user(cls, user):
        profile, _ = cls.objects.get_or_create(user=user)
        return profile


# =================================================================== tickets
def ticket_upload_to(instance, filename):
    """media/tickets/<ticket number>/<random>.<ext>"""
    ext = (filename.rsplit('.', 1)[-1] if '.' in filename else 'dat').lower()[:8]
    number = getattr(instance.message.ticket, 'number', '') or 'misc'
    return f'tickets/{number}/{uuid.uuid4().hex}.{ext}'


TICKET_TOPICS = [
    ('buy_product', 'شراء منتج'),
    ('service', 'طلب خدمة'),
    ('partnership', 'شراكة | إعلانات'),
    ('paid_delivery', 'استلام منتج مدفوع'),
    ('inquiry', 'استفسارات'),
    ('other', 'أخرى'),
]
TICKET_TOPIC_LABELS = {
    'buy_product': ('شراء منتج', 'Buy a product'),
    'service': ('طلب خدمة', 'Request a service'),
    'partnership': ('شراكة | إعلانات', 'Partnership | Ads'),
    'paid_delivery': ('استلام منتج مدفوع', 'Receive a paid product'),
    'inquiry': ('استفسارات', 'Inquiries'),
    'other': ('أخرى', 'Other'),
}
TICKET_STATUSES = [
    ('open', 'مفتوحة'),
    ('answered', 'تم الرد'),
    ('closed', 'مقفولة'),
]
TICKET_STATUS_LABELS = {
    'open': ('مفتوحة', 'Open'),
    'answered': ('تم الرد', 'Answered'),
    'closed': ('مقفولة', 'Closed'),
}

#: what a customer may attach to a ticket message
TICKET_IMAGE_EXTS = ['jpg', 'jpeg', 'png', 'webp', 'gif', 'heic']
TICKET_AUDIO_EXTS = ['webm', 'mp3', 'm4a', 'ogg', 'oga', 'wav', 'aac', 'mp4a']
TICKET_FILE_EXTS = ['pdf', 'doc', 'docx', 'txt', 'xlsx', 'csv', 'zip', 'mp4', 'mov']
TICKET_EXTS = TICKET_IMAGE_EXTS + TICKET_AUDIO_EXTS + TICKET_FILE_EXTS
TICKET_MAX_FILE_MB = 10
TICKET_MAX_FILES = 5


class Ticket(models.Model):
    """A support conversation opened by a signed-in customer."""

    number = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets'
    )
    subject = models.CharField(max_length=160)
    topic = models.CharField(max_length=20, choices=TICKET_TOPICS, default='other')
    order = models.ForeignKey(
        Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets'
    )
    status = models.CharField(max_length=20, choices=TICKET_STATUSES, default='open')
    admin_unread = models.BooleanField(default=True)
    user_unread = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-last_message_at']

    def __str__(self):
        return f'{self.number} — {self.subject}'

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_number():
        while True:
            code = 'TK' + ''.join(random.choices(string.digits, k=6))
            if not Ticket.objects.filter(number=code).exists():
                return code

    def get_absolute_url(self):
        return reverse('support_detail', args=[self.number])

    @property
    def status_label(self):
        return pick(*TICKET_STATUS_LABELS.get(self.status, (self.status, self.status)))

    @property
    def topic_label(self):
        return pick(*TICKET_TOPIC_LABELS.get(self.topic, (self.topic, self.topic)))

    @property
    def is_closed(self):
        return self.status == 'closed'

    @property
    def customer_name(self):
        return self.user.get_full_name() or self.user.first_name or self.user.get_username()

    def touch(self, *, from_staff):
        """Called after a new message: move the status and the unread flags."""
        self.last_message_at = timezone.now()
        if from_staff:
            if self.status != 'closed':
                self.status = 'answered'
            self.user_unread = True
            self.admin_unread = False
        else:
            if self.status != 'closed':
                self.status = 'open'
            self.admin_unread = True
            self.user_unread = False
        self.save(update_fields=['last_message_at', 'status', 'user_unread', 'admin_unread', 'updated_at'])


class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ticket_messages',
    )
    is_staff = models.BooleanField(default=False)
    body = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.ticket.number} — {"المتجر" if self.is_staff else "العميل"}'

    @property
    def author_name(self):
        if self.is_staff:
            return SiteSettings.load().brand_name
        if self.author is None:
            return ''
        return self.author.get_full_name() or self.author.first_name or self.author.get_username()


class TicketAttachment(models.Model):
    KINDS = [('image', 'صورة'), ('audio', 'تسجيل صوتي'), ('file', 'ملف')]

    message = models.ForeignKey(TicketMessage, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(
        upload_to=ticket_upload_to, validators=[FileExtensionValidator(TICKET_EXTS)],
    )
    name = models.CharField(max_length=200, blank=True, default='')
    kind = models.CharField(max_length=10, choices=KINDS, default='file')
    size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.name or self.file.name

    @staticmethod
    def kind_for(filename):
        ext = (filename.rsplit('.', 1)[-1] if '.' in filename else '').lower()
        if ext in TICKET_IMAGE_EXTS:
            return 'image'
        if ext in TICKET_AUDIO_EXTS:
            return 'audio'
        return 'file'

    @property
    def size_label(self):
        size = self.size or 0
        if size >= 1024 * 1024:
            return f'{size / (1024 * 1024):.1f} MB'
        if size >= 1024:
            return f'{size / 1024:.0f} KB'
        return f'{size} B'


# ===================================================================== staff
STAFF_PERMISSIONS = [
    ('orders', 'الطلبات'),
    ('customers', 'العملاء'),
    ('products', 'المنتجات والأقسام والخدمات'),
    ('marketing', 'أكواد الخصم والعروض'),
    ('portfolio', 'أعمالنا'),
    ('reviews', 'تقييمات العملاء'),
    ('content', 'الصفحة الرئيسية والقائمة والسياسات والبانرات'),
    ('messages', 'الرسائل وتذاكر الدعم'),
    ('shipping', 'الدول والشحن'),
    ('settings', 'إعدادات المتجر والدفع'),
    ('staff', 'الإدارة (إضافة وتعديل الإداريين)'),
]
STAFF_PERMISSION_KEYS = [key for key, _ in STAFF_PERMISSIONS]


class StaffProfile(models.Model):
    """Which dashboard sections a staff member may open."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_profile'
    )
    job_title = models.CharField(max_length=80, blank=True, default='')
    permissions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.get_username()} — {", ".join(self.permissions)}'

    @property
    def permission_labels(self):
        labels = dict(STAFF_PERMISSIONS)
        return [labels[p] for p in STAFF_PERMISSION_KEYS if p in (self.permissions or [])]


def staff_permissions(user):
    """Set of section keys `user` may open in the dashboard."""
    if not (user and user.is_authenticated and user.is_active and user.is_staff):
        return set()
    if user.is_superuser:
        return set(STAFF_PERMISSION_KEYS)
    profile = getattr(user, 'staff_profile', None)
    if profile is None:
        # staff accounts created before permissions existed keep full access
        try:
            profile = StaffProfile.objects.get(user=user)
        except StaffProfile.DoesNotExist:
            return set(STAFF_PERMISSION_KEYS)
    return {p for p in (profile.permissions or []) if p in STAFF_PERMISSION_KEYS}


# =================================================================== reviews
class Review(models.Model):
    """A rating left by a customer who paid for an order."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews'
    )
    order = models.OneToOneField(
        Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='review'
    )
    name = models.CharField(max_length=120)
    rating = models.PositiveSmallIntegerField(
        default=5, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    reply = models.TextField(blank=True, default='', help_text='رد المتجر (بيظهر تحت التقييم)')
    is_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.rating}★'

    @property
    def stars(self):
        return range(self.rating)

    @property
    def empty_stars(self):
        return range(5 - self.rating)

    @property
    def initial(self):
        return (self.name or '?').strip()[:1].upper()

    @property
    def avatar_url(self):
        """The customer's picture (uploaded / Google / Discord), if they have one."""
        profile = getattr(self.user, 'customer', None) if self.user_id else None
        return profile.photo_url if profile else ''

    @classmethod
    def published(cls):
        return cls.objects.filter(is_approved=True)

    @classmethod
    def summary(cls):
        qs = cls.published()
        count = qs.count()
        avg = qs.aggregate(a=models.Avg('rating'))['a'] or 0
        dist = {i: 0 for i in range(1, 6)}
        for row in qs.values('rating').annotate(c=models.Count('id')):
            dist[row['rating']] = row['c']
        bars = [
            {'stars': i, 'count': dist[i], 'pct': round(dist[i] * 100 / count) if count else 0}
            for i in range(5, 0, -1)
        ]
        return {'count': count, 'avg': round(avg, 1), 'bars': bars,
                'avg_pct': round(avg * 20) if count else 0}


def two_part_name(first='', last='', fallback=''):
    """First two words of a person's name: «أحمد محمد علي» → «أحمد محمد»."""
    words = f'{first or ""} {last or ""}'.split()
    if len(words) < 2:
        backup = (fallback or '').split('@')[0].split()
        if len(backup) > len(words):
            words = backup
    return ' '.join(words[:2])


def reviewable_orders(user):
    """Paid orders of `user` that do not have a review yet."""
    if not (user and user.is_authenticated):
        return Order.objects.none()
    return Order.objects.filter(user=user, payment_status='paid', review__isnull=True)


# ================================================================= portfolio
class WorkCategory(models.Model):
    name_ar = models.CharField(max_length=80)
    name_en = models.CharField(max_length=80, blank=True, default='')
    slug = models.SlugField(max_length=100, unique=True, blank=True, allow_unicode=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'id']
        verbose_name_plural = 'Work categories'

    def __str__(self):
        return self.name_ar

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name_en or self.name_ar)
        super().save(*args, **kwargs)

    @property
    def name(self):
        return pick(self.name_ar, self.name_en)


class Work(models.Model):
    """One project in the «Our work» gallery."""

    title_ar = models.CharField(max_length=160)
    title_en = models.CharField(max_length=160, blank=True, default='')
    slug = models.SlugField(max_length=190, unique=True, blank=True, allow_unicode=True)
    category = models.ForeignKey(
        WorkCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='works'
    )
    summary_ar = models.CharField(max_length=300, blank=True, default='')
    summary_en = models.CharField(max_length=300, blank=True, default='')
    description_ar = models.TextField(blank=True, default='')
    description_en = models.TextField(blank=True, default='')
    cover = models.ImageField(
        upload_to='works/covers/',
        help_text='البانر — بيظهر فوق صفحة العمل وتحت الرابط لما تبعته لحد',
    )
    client = models.CharField(max_length=120, blank=True, default='')
    work_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text='يظهر في الصفحة الرئيسية')
    ordering = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordering', '-created_at']

    def __str__(self):
        return self.title_ar

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.title_en or self.title_ar)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('work_detail', args=[self.slug])

    @property
    def title(self):
        return pick(self.title_ar, self.title_en)

    @property
    def summary(self):
        return pick(self.summary_ar, self.summary_en)

    @property
    def description(self):
        return pick(self.description_ar, self.description_en)

    @property
    def share_text(self):
        text = self.summary or self.description or ''
        text = ' '.join(text.split())
        return text[:200]

    @property
    def media_count(self):
        return self.media.count()

    @property
    def has_video(self):
        return self.media.filter(kind__in=['video', 'embed']).exists()


VIDEO_FILE_EXTS = ('mp4', 'webm', 'mov', 'm4v', 'ogg', 'ogv')
VIDEO_SITES = 'يوتيوب، فيميو، جوجل درايف، فيسبوك، إنستجرام، تيك توك، ديلي موشن، Streamable، أو لينك مباشر لملف فيديو (mp4)'


def clean_video_url(url):
    """Trim the link and add https:// when it was pasted without it (e.g. «youtu.be/abc»)."""
    url = (url or '').strip().strip('<>"\'')
    if url and not re.match(r'^https?://', url, re.I):
        url = 'https://' + url.lstrip('/')
    return url


def _youtube_id(url):
    match = re.search(
        r'(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/|live/|v/|e/))([\w-]{11})',
        url or '', re.I,
    )
    return match.group(1) if match else ''


def _vimeo_id(url):
    match = re.search(r'vimeo\.com/(?:.*?/)?(?:video/)?(\d{6,})(?:/([\da-f]{6,}))?', url or '', re.I)
    if not match:
        return ''
    vid, hash_ = match.groups()
    return f'{vid}?h={hash_}' if hash_ else vid


def video_embed(url):
    """What a pasted video link turns into on the site.

    Returns {'kind': 'iframe' | 'file', 'src': ..., 'thumb': ...} or None when the link
    isn't a video we can play inside the page.
    """
    from urllib.parse import quote, urlsplit
    url = clean_video_url(url)
    if not url:
        return None
    host = (urlsplit(url).hostname or '').lower()
    path = urlsplit(url).path or ''

    yt = _youtube_id(url)
    if yt:
        return {'kind': 'iframe', 'src': f'https://www.youtube-nocookie.com/embed/{yt}?autoplay=1&rel=0',
                'thumb': f'https://i.ytimg.com/vi/{yt}/hqdefault.jpg'}
    vm = _vimeo_id(url)
    if vm:
        joiner = '&' if '?' in vm else '?'
        return {'kind': 'iframe', 'src': f'https://player.vimeo.com/video/{vm}{joiner}autoplay=1', 'thumb': ''}
    if 'drive.google.com' in host:
        match = re.search(r'/file/d/([\w-]{10,})', url) or re.search(r'[?&]id=([\w-]{10,})', url)
        if match:
            return {'kind': 'iframe', 'src': f'https://drive.google.com/file/d/{match.group(1)}/preview',
                    'thumb': f'https://drive.google.com/thumbnail?id={match.group(1)}&sz=w800'}
    if host.endswith('facebook.com') or host == 'fb.watch':
        return {'kind': 'iframe', 'thumb': '',
                'src': f'https://www.facebook.com/plugins/video.php?href={quote(url, safe="")}&show_text=false&autoplay=true'}
    if host.endswith('instagram.com'):
        match = re.search(r'/(p|reel|reels|tv)/([\w-]+)', path)
        if match:
            kind = 'reel' if match.group(1) in ('reel', 'reels') else match.group(1)
            return {'kind': 'iframe', 'src': f'https://www.instagram.com/{kind}/{match.group(2)}/embed', 'thumb': ''}
    if host.endswith('tiktok.com'):
        match = re.search(r'/video/(\d+)', path)
        if match:
            return {'kind': 'iframe', 'src': f'https://www.tiktok.com/embed/v2/{match.group(1)}', 'thumb': ''}
    if host.endswith('dailymotion.com') or host == 'dai.ly':
        match = re.search(r'(?:/video/|dai\.ly/)([a-z0-9]+)', url, re.I)
        if match:
            return {'kind': 'iframe', 'src': f'https://www.dailymotion.com/embed/video/{match.group(1)}?autoplay=1',
                    'thumb': f'https://www.dailymotion.com/thumbnail/video/{match.group(1)}'}
    if host.endswith('streamable.com'):
        match = re.search(r'streamable\.com/(?:e/)?([a-z0-9]+)', url, re.I)
        if match:
            return {'kind': 'iframe', 'src': f'https://streamable.com/e/{match.group(1)}?autoplay=1', 'thumb': ''}
    if path.rsplit('.', 1)[-1].lower() in VIDEO_FILE_EXTS:
        return {'kind': 'file', 'src': url, 'thumb': ''}
    return None


class WorkMedia(models.Model):
    KINDS = [
        ('image', 'صورة'),
        ('video', 'فيديو مرفوع'),
        ('embed', 'فيديو من لينك'),
    ]

    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name='media')
    kind = models.CharField(max_length=10, choices=KINDS, default='image')
    image = models.ImageField(upload_to='works/media/', blank=True, null=True)
    video = models.FileField(
        upload_to='works/videos/', blank=True, null=True,
        validators=[FileExtensionValidator(['mp4', 'webm', 'mov', 'm4v'])],
    )
    poster = models.ImageField(
        upload_to='works/posters/', blank=True, null=True,
        help_text='صورة غلاف للفيديو (اختياري)',
    )
    embed_url = models.URLField(max_length=1000, blank=True, default='')
    caption_ar = models.CharField(max_length=200, blank=True, default='')
    caption_en = models.CharField(max_length=200, blank=True, default='')
    ordering = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordering', 'id']

    def __str__(self):
        return f'{self.get_kind_display()} — {self.work}'

    @property
    def caption(self):
        return pick(self.caption_ar, self.caption_en)

    @property
    def is_video(self):
        return self.kind in ('video', 'embed')

    @property
    def embed_info(self):
        if not hasattr(self, '_embed_info'):
            self._embed_info = video_embed(self.embed_url) if self.kind == 'embed' else None
        return self._embed_info

    @property
    def embed_src(self):
        info = self.embed_info
        return info['src'] if info else self.embed_url

    @property
    def inline_src(self):
        """The player for an iframe shown right in the page (no autoplay)."""
        src = self.embed_src
        return src.replace('?autoplay=1&', '?').replace('?autoplay=1', '').replace('&autoplay=1', '').replace('&autoplay=true', '')

    @property
    def is_iframe(self):
        return self.play_kind == 'embed'

    @property
    def is_tall(self):
        """Instagram / TikTok players are portrait."""
        src = self.embed_src or ''
        return 'instagram.com' in src or 'tiktok.com' in src

    @property
    def play_kind(self):
        """How the lightbox plays it: image | video (a file) | embed (a player in an iframe)."""
        if self.kind == 'embed':
            info = self.embed_info
            return 'video' if info and info['kind'] == 'file' else 'embed'
        return self.kind

    @property
    def thumb_url(self):
        if self.kind == 'image' and self.image:
            return self.image.url
        if self.poster:
            return self.poster.url
        info = self.embed_info
        return info['thumb'] if info else ''

    @property
    def full_url(self):
        if self.kind == 'image' and self.image:
            return self.image.url
        if self.kind == 'video' and self.video:
            return self.video.url
        return self.embed_src


# ================================================================== homepage
HOME_SECTIONS = [
    ('hero', 'الواجهة الرئيسية (Hero)'),
    ('banners', 'سلايدر البانرات'),
    ('features', 'مميزات المتجر'),
    ('categories', 'الأقسام'),
    ('featured', 'منتجات مختارة'),
    ('about', 'من نحن'),
    ('portfolio', 'أعمالنا'),
    ('sale', 'العروض'),
    ('new_arrivals', 'وصل حديثًا'),
    ('reviews', 'تقييمات العملاء'),
]

# key: (eyebrow ar/en, title ar/en, subtitle ar/en, button ar/en, link, limit)
HOME_SECTION_DEFAULTS = {
    'hero': ('استوديو جرافيك', 'CREATIVE STUDIO', 'صمّم\nهويتك', 'DESIGN YOUR\nIDENTITY',
             'لوجوهات وسوشيال ميديا وتصميمات طباعة — بألوانك وعلى ذوقك.',
             'Logos, social media & print — designed in your colors.',
             'اكتشف التصميمات', 'EXPLORE DESIGNS', '/shop/', 0),
    'banners': ('', '', '', '', '', '', '', '', '', 0),
    'features': ('', '', '', '', '', '', '', '', '', 4),
    'categories': ('الأقسام', 'Categories', 'تصفح الأقسام', 'Browse categories',
                   'اختار القسم اللي يناسب ستايلك', 'Pick the section that fits your style',
                   '', '', '', 6),
    'featured': ('مختارات', 'Featured', 'منتجات مختارة', 'Featured pieces',
                 'قطع اخترناها لك من أحدث المجموعات', 'Hand-picked pieces from our latest drops',
                 'عرض الكل', 'View all', '/shop/', 8),
    'about': ('من نحن', 'About us', 'حكايتنا', 'Our story',
              '', '', 'اعرف أكتر', 'Learn more', '/about/', 0),
    'portfolio': ('أعمالنا', 'Our work', 'من أعمالنا', 'Selected work',
                  'لقطات من شغلنا — صور وفيديوهات', 'Moments from our work — photos and films',
                  'كل الأعمال', 'All work', '/works/', 5),
    'sale': ('العروض', 'Sale', 'عروض لفترة محدودة', 'Limited-time offers',
             '', '', 'عرض الكل', 'View all', '/shop/?sale=1', 8),
    'new_arrivals': ('جديد', 'New', 'وصل حديثًا', 'New arrivals',
                     'آخر ما وصل إلى المتجر', 'The latest to land in store',
                     'عرض الكل', 'View all', '/shop/?sort=new', 8),
    'reviews': ('تقييمات العملاء', 'Reviews', 'آراء عملائنا', 'What our customers say',
                'تقييمات حقيقية من عملاء اشتروا من المتجر', 'Real ratings from verified buyers',
                'كل التقييمات', 'All reviews', '/reviews/', 6),
}


class HomeSection(models.Model):
    """One block of the homepage — the owner orders, hides and retitles them."""

    key = models.CharField(max_length=30, unique=True, choices=HOME_SECTIONS)
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)
    eyebrow_ar = models.CharField(max_length=80, blank=True, default='')
    eyebrow_en = models.CharField(max_length=80, blank=True, default='')
    title_ar = models.CharField(
        max_length=200, blank=True, default='',
        help_text='في الـ Hero: السطر التاني بعد Enter بيتلوّن',
    )
    title_en = models.CharField(max_length=200, blank=True, default='')
    subtitle_ar = models.TextField(blank=True, default='')
    subtitle_en = models.TextField(blank=True, default='')
    button_text_ar = models.CharField(max_length=60, blank=True, default='')
    button_text_en = models.CharField(max_length=60, blank=True, default='')
    button_link = models.CharField(max_length=255, blank=True, default='')
    image = models.ImageField(upload_to='home/', blank=True, null=True)
    # hero only: a separate picture for phones, where the photo sits in the frame, the handwritten words
    image_mobile = models.ImageField(upload_to='home/', blank=True, null=True)
    image_focus = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MaxValueValidator(100)],
    )
    image_focus_mobile = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MaxValueValidator(100)],
    )
    script_text = models.CharField(max_length=160, blank=True, default='')
    items_limit = models.PositiveSmallIntegerField(default=8)

    class Meta:
        ordering = ['ordering', 'id']

    def __str__(self):
        return self.get_key_display()

    @property
    def eyebrow(self):
        return pick(self.eyebrow_ar, self.eyebrow_en)

    @property
    def title(self):
        return pick(self.title_ar, self.title_en)

    # -- hero: always English, whatever the page language (owner's choice)
    @staticmethod
    def _lines(text):
        lines = [line.strip() for line in (text or '').replace('\\n', '\n').splitlines()]
        lines = [line for line in lines if line]
        if not lines:
            return '', ''
        return lines[0], ' '.join(lines[1:])

    @property
    def hero_eyebrow(self):
        return self.eyebrow_en or self.eyebrow_ar

    @property
    def hero_lines(self):
        return self._lines(self.title_en or self.title_ar)

    @property
    def hero_subtitle(self):
        return self.subtitle_en or self.subtitle_ar

    @property
    def hero_button(self):
        return self.button_text_en or self.button_text_ar

    @property
    def hero_script(self):
        """The handwritten words on the right of the hero (big screens) — one word per line."""
        return (self.script_text or '').replace('\\n', '\n').strip()

    @property
    def title_lines(self):
        lines = [line.strip() for line in (self.title or '').replace('\\n', '\n').splitlines()]
        lines = [line for line in lines if line]
        if not lines:
            return '', ''
        return lines[0], ' '.join(lines[1:])

    @property
    def subtitle(self):
        return pick(self.subtitle_ar, self.subtitle_en)

    @property
    def button_text(self):
        return pick(self.button_text_ar, self.button_text_en)

    @property
    def label(self):
        return self.get_key_display()

    @property
    def uses_limit(self):
        return self.key in ('categories', 'featured', 'portfolio', 'sale', 'new_arrivals', 'reviews')

    @property
    def uses_image(self):
        return self.key in ('hero', 'about')

    @classmethod
    def ensure_defaults(cls):
        existing = set(cls.objects.values_list('key', flat=True))
        for index, (key, _) in enumerate(HOME_SECTIONS):
            if key in existing:
                continue
            d = HOME_SECTION_DEFAULTS.get(key, ('',) * 9 + (8,))
            cls.objects.create(
                key=key, ordering=index,
                eyebrow_ar=d[0], eyebrow_en=d[1], title_ar=d[2], title_en=d[3],
                subtitle_ar=d[4], subtitle_en=d[5], button_text_ar=d[6], button_text_en=d[7],
                button_link=d[8], items_limit=d[9] or 8,
            )


# ============================================================= about / story
ABOUT_STATS_MODES = [
    ('auto', 'أرقام تلقائية (عدد العملاء والديزاينات والأعمال والتقييم)'),
    ('custom', 'أرقام أنا اللي بكتبها'),
    ('hidden', 'من غير أرقام'),
]


class AboutPage(models.Model):
    """Everything in «حكايتنا» that isn't in the homepage block itself (one row)."""

    tag_ar = models.CharField(max_length=80, blank=True, default='')
    tag_en = models.CharField(max_length=80, blank=True, default='')
    show_tag = models.BooleanField(default=True)
    stats_mode = models.CharField(max_length=10, choices=ABOUT_STATS_MODES, default='auto')
    stats_on_home = models.BooleanField(default=True)
    stats_on_page = models.BooleanField(default=True)
    # «أرقام تلقائية»: leave empty for the real number, or write your own
    customers_override = models.PositiveIntegerField(null=True, blank=True)
    products_override = models.PositiveIntegerField(null=True, blank=True)
    works_override = models.PositiveIntegerField(null=True, blank=True)
    # the /about/ page
    page_title_ar = models.CharField(max_length=160, blank=True, default='')
    page_title_en = models.CharField(max_length=160, blank=True, default='')
    page_subtitle_ar = models.CharField(max_length=300, blank=True, default='')
    page_subtitle_en = models.CharField(max_length=300, blank=True, default='')
    page_image = models.ImageField(upload_to='site/', blank=True, null=True)
    button1_text_ar = models.CharField(max_length=60, blank=True, default='تسوّق الآن')
    button1_text_en = models.CharField(max_length=60, blank=True, default='Shop now')
    button1_link = models.CharField(max_length=300, blank=True, default='/shop/')
    button2_text_ar = models.CharField(max_length=60, blank=True, default='أعمالنا')
    button2_text_en = models.CharField(max_length=60, blank=True, default='Our work')
    button2_link = models.CharField(max_length=300, blank=True, default='/works/')
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def tag(self):
        return pick(self.tag_ar, self.tag_en)

    @property
    def page_title(self):
        return pick(self.page_title_ar, self.page_title_en)

    @property
    def page_subtitle(self):
        return pick(self.page_subtitle_ar, self.page_subtitle_en)

    @property
    def buttons(self):
        out = []
        for n, ghost in ((1, False), (2, True)):
            text = pick(getattr(self, f'button{n}_text_ar'), getattr(self, f'button{n}_text_en'))
            link = getattr(self, f'button{n}_link')
            if text and link:
                out.append({'text': text, 'link': link, 'ghost': ghost})
        return out


class AboutStat(models.Model):
    """A number the owner writes himself in «حكايتنا» (e.g. 500+ عميل)."""

    value = models.CharField(max_length=20)
    suffix = models.CharField(max_length=6, blank=True, default='+', help_text='مثلاً + أو % أو K')
    show_star = models.BooleanField(default=False)
    label_ar = models.CharField(max_length=60)
    label_en = models.CharField(max_length=60, blank=True, default='')
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'id']

    def __str__(self):
        return f'{self.value}{self.suffix} {self.label_ar}'

    @property
    def label(self):
        return pick(self.label_ar, self.label_en)


# ==================================================================== navbar
NAV_TYPES = [
    ('home', 'الرئيسية'),
    ('shop', 'المتجر'),
    ('new', 'وصل حديثًا'),
    ('sale', 'العروض'),
    ('portfolio', 'أعمالنا'),
    ('reviews', 'تقييمات العملاء'),
    ('about', 'من نحن'),
    ('contact', 'اتصل بنا'),
    ('track', 'تتبع الطلب'),
    ('support', 'الدعم والتذاكر'),
    ('category', 'قسم من المتجر'),
    ('policy', 'صفحة سياسة'),
    ('custom', 'رابط مخصص'),
]

# default label (ar, en) + url name for the built-in types
NAV_BUILTINS = {
    'home': ('الرئيسية', 'Home', 'home', ''),
    'shop': ('المتجر', 'Shop', 'shop', ''),
    'new': ('وصل حديثًا', 'New', 'shop', '?sort=new'),
    'sale': ('العروض', 'Sale', 'shop', '?sale=1'),
    'portfolio': ('أعمالنا', 'Our work', 'works', ''),
    'reviews': ('آراء العملاء', 'Reviews', 'reviews', ''),
    'about': ('من نحن', 'About', 'about', ''),
    'contact': ('اتصل بنا', 'Contact', 'contact', ''),
    'track': ('تتبع طلبك', 'Track order', 'track_order', ''),
    'support': ('الدعم', 'Support', 'support', ''),
}


class Policy(models.Model):
    """Store policies (privacy, returns, shipping…) — the owner writes the text."""

    title_ar = models.CharField(max_length=160)
    title_en = models.CharField(max_length=160, blank=True, default='')
    slug = models.SlugField(max_length=190, unique=True, blank=True, allow_unicode=True)
    content_ar = models.TextField(blank=True, default='')
    content_en = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    show_in_footer = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordering', 'id']
        verbose_name_plural = 'Policies'

    def __str__(self):
        return self.title_ar

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.title_en or self.title_ar)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('policy_detail', args=[self.slug])

    @property
    def title(self):
        return pick(self.title_ar, self.title_en)

    @property
    def content(self):
        return pick(self.content_ar, self.content_en)

    @property
    def has_content(self):
        return bool((self.content_ar or '').strip() or (self.content_en or '').strip())


# ============================================================ link previews
def normalize_site_path(value):
    """'https://site.com/policies/x/?lang=ar' → '/policies/x/' (what request.path looks like)."""
    from urllib.parse import unquote, urlsplit
    value = (value or '').strip()
    if not value:
        return '/'
    parts = urlsplit(value if '://' in value else 'http://x' + ('' if value.startswith('/') else '/') + value)
    path = unquote(parts.path or '/')
    if not path.startswith('/'):
        path = '/' + path
    if not path.endswith('/') and '.' not in path.rsplit('/', 1)[-1]:
        path += '/'
    return path


class LinkPreview(models.Model):
    """The picture / title that shows under a link when it's shared (WhatsApp, Facebook…)."""

    path = models.CharField(max_length=300, unique=True)
    match_children = models.BooleanField(
        default=False, help_text='مثلاً /policies/ → كل صفحات السياسات تاخد نفس الصورة'
    )
    image = models.ImageField(upload_to='share/')
    title_ar = models.CharField(max_length=160, blank=True, default='')
    title_en = models.CharField(max_length=160, blank=True, default='')
    description_ar = models.CharField(max_length=300, blank=True, default='')
    description_en = models.CharField(max_length=300, blank=True, default='')
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['path']

    def __str__(self):
        return self.path

    def save(self, *args, **kwargs):
        self.path = normalize_site_path(self.path)
        super().save(*args, **kwargs)

    @property
    def title(self):
        return pick(self.title_ar, self.title_en)

    @property
    def description(self):
        return pick(self.description_ar, self.description_en)

    @classmethod
    def for_path(cls, path):
        """Exact link first, then the longest parent marked «ينطبق على الصفحات اللي جواه»."""
        path = normalize_site_path(path)
        items = list(cls.objects.filter(is_active=True).only(
            'path', 'match_children', 'image', 'title_ar', 'title_en', 'description_ar', 'description_en',
        ))
        exact = next((i for i in items if i.path == path), None)
        if exact:
            return exact
        parents = [i for i in items if i.match_children and path.startswith(i.path)]
        return max(parents, key=lambda i: len(i.path)) if parents else None


class NavLink(models.Model):
    """An item of the header menu (desktop bar + mobile drawer)."""

    link_type = models.CharField(max_length=12, choices=NAV_TYPES, default='custom')
    label_ar = models.CharField(max_length=60, blank=True, default='', help_text='اتركه فاضي للاسم الافتراضي')
    label_en = models.CharField(max_length=60, blank=True, default='')
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, null=True, blank=True, related_name='nav_links'
    )
    policy = models.ForeignKey(
        Policy, on_delete=models.CASCADE, null=True, blank=True, related_name='nav_links'
    )
    url = models.CharField(max_length=255, blank=True, default='', help_text='للرابط المخصص فقط')
    new_tab = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'id']

    def __str__(self):
        return self.label or self.get_link_type_display()

    @property
    def label(self):
        if self.label_ar or self.label_en:
            return pick(self.label_ar, self.label_en)
        if self.link_type in NAV_BUILTINS:
            ar, en, _, _ = NAV_BUILTINS[self.link_type]
            return pick(ar, en)
        if self.link_type == 'category' and self.category:
            return self.category.name
        if self.link_type == 'policy' and self.policy:
            return self.policy.title
        return self.url

    @property
    def href(self):
        if self.link_type in NAV_BUILTINS:
            _, _, name, query = NAV_BUILTINS[self.link_type]
            return reverse(name) + query
        if self.link_type == 'category' and self.category:
            return reverse('category_detail', args=[self.category.slug])
        if self.link_type == 'policy' and self.policy:
            return self.policy.get_absolute_url()
        return self.url or '#'

    @property
    def is_visible(self):
        if not self.is_active:
            return False
        if self.link_type == 'category':
            return bool(self.category and self.category.is_active)
        if self.link_type == 'policy':
            return bool(self.policy and self.policy.is_active)
        return True

    #: what a fresh store starts with — «الدعم» is there so customers find it
    DEFAULT_KEYS = ['home', 'shop', 'portfolio', 'sale', 'reviews', 'support', 'about', 'contact']

    @classmethod
    def ensure_defaults(cls):
        if cls.objects.exists():
            return
        for index, key in enumerate(cls.DEFAULT_KEYS):
            cls.objects.create(link_type=key, ordering=index)

    @classmethod
    def ensure_support_link(cls):
        """Add the «الدعم» item to an existing menu (once) — staff never see it."""
        if cls.objects.filter(link_type='support').exists():
            return None
        last = cls.objects.order_by('-ordering').values_list('ordering', flat=True).first() or 0
        return cls.objects.create(link_type='support', ordering=last + 1)


DEFAULT_POLICIES = [
    ('سياسة الخصوصية', 'Privacy policy', 'privacy-policy'),
    ('سياسة الاستبدال والاسترجاع', 'Returns & exchanges', 'returns-policy'),
    ('سياسة الشحن والتوصيل', 'Shipping policy', 'shipping-policy'),
    ('الشروط والأحكام', 'Terms & conditions', 'terms'),
]


def ensure_policy_defaults():
    if Policy.objects.exists():
        return
    for index, (ar, en, slug) in enumerate(DEFAULT_POLICIES):
        Policy.objects.create(title_ar=ar, title_en=en, slug=slug, ordering=index)
