"""Dashboard forms.

The storefront is Arabic by default with an English switch, so every
translatable field comes in a pair: `<name>_ar` (required where the model
requires it) and `<name>_en` (optional — the site falls back to Arabic).
`dashboard/_form_fields.html` renders each pair side by side.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import normalize_site_path
from .models import (
    AboutPage, AboutStat, Announcement, Banner, Category, Country, Coupon, HomeSection, LinkPreview, NavLink, Order, Policy,
    Product, ProductColor, Promotion, Review, STAFF_PERMISSIONS, Service, SiteSettings,
    Work, WorkCategory,
)

DATETIME_FORMATS = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
EN_HELP = 'اختياري — لو فاضي هيظهر النص العربي في النسخة الإنجليزية'


class StyledForm(forms.ModelForm):
    """Attaches the dashboard CSS classes + language hints to every widget."""

    #: fields the model marks optional but the dashboard must require
    REQUIRED = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.REQUIRED:
            if name in self.fields:
                self.fields[name].required = True
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'switch-input')
            elif isinstance(widget, forms.CheckboxSelectMultiple):
                widget.attrs.setdefault('class', 'check-list')
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault('class', 'inp select')
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault('class', 'inp area')
                widget.attrs.setdefault('rows', 4)
            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs.setdefault('class', 'inp file')
            else:
                widget.attrs.setdefault('class', 'inp')
            if isinstance(widget, forms.DateTimeInput):
                widget.input_type = 'datetime-local'
                widget.format = '%Y-%m-%dT%H:%M'

            if name.endswith('_ar'):
                field.lang = 'ar'
                widget.attrs.setdefault('dir', 'rtl')
            elif name.endswith('_en'):
                field.lang = 'en'
                widget.attrs.setdefault('dir', 'ltr')
                if not field.required and not field.help_text:
                    field.help_text = EN_HELP


# ================================================================== catalogue
class ProductForm(StyledForm):
    class Meta:
        model = Product
        fields = [
            'name_ar', 'name_en', 'category', 'sku', 'price', 'compare_price',
            'short_ar', 'short_en', 'description_ar', 'description_en',
            'is_active', 'is_featured', 'is_new', 'ordering', 'slug',
        ]
        widgets = {
            'description_ar': forms.Textarea(attrs={'rows': 5}),
            'description_en': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'name_ar': 'اسم المنتج', 'name_en': 'اسم المنتج',
            'category': 'القسم', 'sku': 'كود المنتج (SKU)',
            'price': 'السعر', 'compare_price': 'السعر قبل الخصم (اختياري)',
            'short_ar': 'وصف مختصر', 'short_en': 'وصف مختصر',
            'description_ar': 'الوصف الكامل', 'description_en': 'الوصف الكامل',
            'is_active': 'معروض في المتجر', 'is_featured': 'منتج مميز',
            'is_new': 'علامة «جديد»', 'ordering': 'ترتيب الظهور', 'slug': 'الرابط (slug)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = '— بدون قسم —'


class CategoryForm(StyledForm):
    class Meta:
        model = Category
        fields = [
            'name_ar', 'name_en', 'slug', 'description_ar', 'description_en',
            'image', 'is_active', 'is_featured', 'ordering',
        ]
        labels = {
            'name_ar': 'اسم القسم', 'name_en': 'اسم القسم', 'slug': 'الرابط (slug)',
            'description_ar': 'الوصف', 'description_en': 'الوصف',
            'image': 'صورة القسم', 'is_active': 'مفعّل',
            'is_featured': 'يظهر في الصفحة الرئيسية', 'ordering': 'الترتيب',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False


class ColorForm(StyledForm):
    class Meta:
        model = ProductColor
        fields = ['name_ar', 'name_en', 'hex_code']
        widgets = {'hex_code': forms.TextInput(attrs={'type': 'color'})}
        labels = {'name_ar': 'اسم اللون', 'name_en': 'اسم اللون', 'hex_code': 'الكود اللوني'}


class ServiceForm(StyledForm):
    """A service the customer picks on a design — Malak writes them himself."""

    class Meta:
        model = Service
        fields = ['name_ar', 'name_en', 'price', 'is_active', 'ordering']
        labels = {
            'name_ar': 'اسم الخدمة', 'name_en': 'اسم الخدمة',
            'price': 'سعر إضافي', 'is_active': 'متاحة للعملاء', 'ordering': 'الترتيب',
        }
        help_texts = {
            'price': 'بيتزوّد على سعر الديزاين — سيبه 0 لو الخدمة من غير زيادة',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['price'].widget.attrs.update({'min': '0', 'step': '0.01'})

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError('السعر الإضافي ما ينفعش يبقى بالسالب')
        return price


# ================================================================== marketing
class CouponForm(StyledForm):
    class Meta:
        model = Coupon
        fields = [
            'code', 'description', 'discount_type', 'value', 'min_order',
            'free_shipping', 'max_uses', 'categories', 'start_at', 'end_at', 'is_active',
        ]
        widgets = {
            'categories': forms.CheckboxSelectMultiple(),
            'start_at': forms.DateTimeInput(),
            'end_at': forms.DateTimeInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('start_at', 'end_at'):
            self.fields[name].input_formats = DATETIME_FORMATS


class PromotionForm(StyledForm):
    class Meta:
        model = Promotion
        fields = [
            'title', 'scope', 'discount_type', 'value', 'categories', 'products',
            'badge_ar', 'badge_en', 'start_at', 'end_at', 'is_active',
        ]
        widgets = {
            'categories': forms.CheckboxSelectMultiple(),
            'products': forms.SelectMultiple(attrs={'size': 10}),
            'start_at': forms.DateTimeInput(),
            'end_at': forms.DateTimeInput(),
        }
        labels = {'badge_ar': 'شارة العرض', 'badge_en': 'شارة العرض'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['products'].queryset = Product.objects.all()
        for name in ('start_at', 'end_at'):
            self.fields[name].input_formats = DATETIME_FORMATS


class AnnouncementForm(StyledForm):
    class Meta:
        model = Announcement
        fields = ['text_ar', 'text_en', 'link', 'is_active', 'ordering']
        labels = {
            'text_ar': 'نص الإعلان', 'text_en': 'نص الإعلان', 'link': 'رابط (اختياري)',
            'is_active': 'ظاهر في الشريط', 'ordering': 'الترتيب',
        }


class LinkPreviewForm(StyledForm):
    class Meta:
        model = LinkPreview
        fields = [
            'path', 'match_children', 'image', 'title_ar', 'title_en',
            'description_ar', 'description_en', 'is_active',
        ]
        widgets = {
            'path': forms.TextInput(attrs={'dir': 'ltr', 'list': 'site-pages',
                                           'placeholder': '/policies/privacy/  أو الرابط كامل'}),
        }
        labels = {
            'path': 'الرابط', 'match_children': 'ينطبق كمان على كل الصفحات اللي جوه الرابط ده',
            'image': 'الصورة اللي تظهر مع الرابط', 'title_ar': 'العنوان (اختياري)',
            'title_en': 'العنوان (اختياري)', 'description_ar': 'الوصف (اختياري)',
            'description_en': 'الوصف (اختياري)', 'is_active': 'مفعّل',
        }
        help_texts = {
            'path': 'الصق رابط الصفحة من الموقع أو اكتب آخره بس — مثلاً / للصفحة الرئيسية',
            'image': 'المقاس المثالي 1200×630',
            'title_ar': 'لو فاضي هيظهر عنوان الصفحة العادي',
        }

    def clean_path(self):
        path = normalize_site_path(self.cleaned_data.get('path'))
        if path.startswith('/dashboard'):
            raise forms.ValidationError('ده رابط لوحة التحكم — اختار رابط من الموقع')
        qs = LinkPreview.objects.filter(path=path)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('الرابط ده عليه صورة قبل كده — عدّلها من القائمة')
        return path


class DefaultShareImageForm(StyledForm):
    class Meta:
        model = SiteSettings
        fields = ['share_image']
        labels = {'share_image': 'الصورة الافتراضية'}
        help_texts = {'share_image': 'بتظهر مع أي رابط من الموقع ملوش صورة خاصة (1200×630 مثالي)'}


class BannerForm(StyledForm):
    class Meta:
        model = Banner
        fields = [
            'title_ar', 'title_en', 'subtitle_ar', 'subtitle_en',
            'button_text_ar', 'button_text_en', 'link', 'image', 'is_active', 'ordering',
        ]
        labels = {
            'title_ar': 'العنوان', 'title_en': 'العنوان',
            'subtitle_ar': 'العنوان الفرعي', 'subtitle_en': 'العنوان الفرعي',
            'button_text_ar': 'نص الزرار', 'button_text_en': 'نص الزرار', 'link': 'الرابط',
            'image': 'الصورة', 'is_active': 'ظاهر', 'ordering': 'الترتيب',
        }


class CountryForm(StyledForm):
    class Meta:
        model = Country
        fields = [
            'name_ar', 'name_en', 'code', 'shipping_fee', 'free_shipping_over',
            'delivery_ar', 'delivery_en', 'is_active', 'ordering',
        ]
        widgets = {
            'code': forms.TextInput(attrs={'dir': 'ltr', 'maxlength': 2, 'placeholder': 'SA'}),
            'delivery_ar': forms.TextInput(attrs={'placeholder': 'مثلاً: من 7 لـ 10 أيام عمل'}),
            'delivery_en': forms.TextInput(attrs={'placeholder': 'e.g. 7–10 business days'}),
        }
        labels = {
            'name_ar': 'اسم الدولة', 'name_en': 'اسم الدولة',
            'code': 'كود الدولة (اختياري)',
            'shipping_fee': 'سعر الشحن للدولة دي',
            'free_shipping_over': 'شحن مجاني فوق مبلغ (للدولة دي)',
            'delivery_ar': 'مدة التوصيل', 'delivery_en': 'مدة التوصيل',
            'is_active': 'متاحة للشحن', 'ordering': 'الترتيب',
        }
        help_texts = {
            'code': 'حرفين زي EG أو SA — اختياري',
            'shipping_fee': 'فاضي = سعر الشحن العام من الإعدادات',
            'free_shipping_over': 'فاضي = حد الشحن المجاني العام · 0 = مفيش شحن مجاني للدولة دي',
            'delivery_ar': 'اختياري — بيظهر للعميل تحت اختيار الدولة',
            'ordering': 'الرقم الأصغر يظهر الأول (الافتراضي 100)',
        }

    def clean_code(self):
        code = (self.cleaned_data.get('code') or '').strip().upper()
        if code and (len(code) != 2 or not code.isalpha()):
            raise forms.ValidationError('الكود لازم يكون حرفين إنجليزي زي EG')
        if code and Country.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('الكود ده مستخدم لدولة تانية')
        return code



class NotificationSettingsForm(StyledForm):
    """«الإشعارات والإيميل» — Gmail (or any SMTP) + what deserves an email."""

    class Meta:
        model = SiteSettings
        fields = [
            'emails_enabled', 'notify_email', 'site_url',
            'notify_new_order', 'notify_new_ticket', 'notify_new_message', 'notify_new_review',
            'notify_customer_order', 'notify_customer_ticket',
            'smtp_host', 'smtp_port', 'smtp_user', 'smtp_password', 'smtp_use_tls',
        ]
        widgets = {
            'notify_email': forms.EmailInput(attrs={'dir': 'ltr', 'placeholder': 'you@gmail.com'}),
            'site_url': forms.TextInput(attrs={'dir': 'ltr', 'placeholder': 'https://rgstower.com'}),
            'smtp_host': forms.TextInput(attrs={'dir': 'ltr'}),
            'smtp_port': forms.NumberInput(attrs={'dir': 'ltr'}),
            'smtp_user': forms.TextInput(attrs={'dir': 'ltr', 'placeholder': 'you@gmail.com', 'autocomplete': 'off'}),
            'smtp_password': forms.PasswordInput(
                attrs={'dir': 'ltr', 'autocomplete': 'new-password', 'placeholder': '••••••••••••••••'},
                render_value=True,
            ),
        }
        labels = {
            'emails_enabled': 'تشغيل الإيميلات',
            'notify_email': 'إيميل استقبال الإشعارات',
            'site_url': 'لينك المتجر',
            'notify_new_order': 'إشعار بكل طلب جديد',
            'notify_new_ticket': 'إشعار بالتذاكر وردود العملاء',
            'notify_new_message': 'إشعار برسايل «اتصل بنا»',
            'notify_new_review': 'إشعار بالتقييمات الجديدة',
            'notify_customer_order': 'إرسال تأكيد الطلب للعميل',
            'notify_customer_ticket': 'إبلاغ العميل لما ترد على تذكرته',
            'smtp_host': 'SMTP host', 'smtp_port': 'SMTP port',
            'smtp_user': 'الإيميل اللي هيبعت', 'smtp_password': 'App password',
            'smtp_use_tls': 'TLS (بورت 587)',
        }
        help_texts = {
            'notify_email': 'ممكن يكون نفس الجيميل اللي بيبعت',
            'site_url': 'علشان اللينكات اللي جوه الإيميل تشتغل صح',
            'smtp_password': 'من حساب جوجل: الأمان ← التحقق بخطوتين ← App passwords (16 حرف من غير مسافات)',
            'smtp_use_tls': 'سيبها مفتوحة مع بورت 587 · اقفلها لو بتستخدم 465 (SSL)',
        }

    def clean_smtp_password(self):
        return (self.cleaned_data.get('smtp_password') or '').replace(' ', '')


class GoogleLoginForm(StyledForm):
    """«الدخول بجوجل» — مفاتيح OAuth من Google Cloud Console."""

    google_client_secret = forms.CharField(
        label='Client secret', required=False,
        widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'new-password', 'dir': 'ltr'}),
        help_text='سيبه فاضي علشان يفضل المحفوظ زي ما هو',
    )

    class Meta:
        model = SiteSettings
        fields = ['google_login_enabled', 'google_client_id', 'google_client_secret']
        labels = {
            'google_login_enabled': 'تفعيل الدخول بحساب جوجل',
            'google_client_id': 'Client ID',
        }
        help_texts = {
            'google_client_id': 'بينتهي بـ .apps.googleusercontent.com',
        }
        widgets = {
            'google_client_id': forms.TextInput(attrs={
                'dir': 'ltr', 'autocomplete': 'off',
                'placeholder': '1234567890-xxxxxxxx.apps.googleusercontent.com',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.google_client_secret:
            self.fields['google_client_secret'].widget.attrs['placeholder'] = '•••••••• (محفوظ)'

    def clean_google_client_id(self):
        return (self.cleaned_data.get('google_client_id') or '').strip()

    def clean_google_client_secret(self):
        """Blank means «keep the saved one» — the field never shows it back."""
        value = (self.cleaned_data.get('google_client_secret') or '').strip()
        return value or self.instance.google_client_secret

    def clean(self):
        data = super().clean()
        if data.get('google_login_enabled') and not (
            data.get('google_client_id') and data.get('google_client_secret')
        ):
            raise forms.ValidationError(
                'علشان تشغّل الدخول بجوجل لازم تحط الـ Client ID والـ Client secret الأول'
            )
        return data


class DiscordLoginForm(StyledForm):
    """«الدخول بديسكورد» — مفاتيح OAuth2 من Discord Developer Portal."""

    discord_client_secret = forms.CharField(
        label='Client secret', required=False,
        widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'new-password', 'dir': 'ltr'}),
        help_text='سيبه فاضي علشان يفضل المحفوظ زي ما هو',
    )

    class Meta:
        model = SiteSettings
        fields = ['discord_login_enabled', 'discord_client_id', 'discord_client_secret']
        labels = {
            'discord_login_enabled': 'تفعيل الدخول بحساب ديسكورد',
            'discord_client_id': 'Client ID',
        }
        help_texts = {
            'discord_client_id': 'رقم طويل من OAuth2 ← Client information (هو نفسه الـ Application ID)',
        }
        widgets = {
            'discord_client_id': forms.TextInput(attrs={
                'dir': 'ltr', 'autocomplete': 'off', 'inputmode': 'numeric',
                'placeholder': '123456789012345678',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.discord_client_secret:
            self.fields['discord_client_secret'].widget.attrs['placeholder'] = '•••••••• (محفوظ)'

    def clean_discord_client_id(self):
        value = (self.cleaned_data.get('discord_client_id') or '').strip()
        if value and not value.isdigit():
            raise forms.ValidationError('الـ Client ID بتاع ديسكورد أرقام بس — انسخه من صفحة OAuth2')
        return value

    def clean_discord_client_secret(self):
        """Blank means «keep the saved one» — the field never shows it back."""
        value = (self.cleaned_data.get('discord_client_secret') or '').strip()
        return value or self.instance.discord_client_secret

    def clean(self):
        data = super().clean()
        if data.get('discord_login_enabled') and not (
            data.get('discord_client_id') and data.get('discord_client_secret')
        ):
            raise forms.ValidationError(
                'علشان تشغّل الدخول بديسكورد لازم تحط الـ Client ID والـ Client secret الأول'
            )
        return data


# =================================================================== settings
class SiteSettingsForm(StyledForm):
    REQUIRED = ('brand_name_ar',)

    class Meta:
        model = SiteSettings
        fields = [
            'brand_name_ar', 'brand_name_en', 'tagline_ar', 'tagline_en',
            'logo', 'favicon', 'share_image',
            'phone', 'whatsapp', 'email', 'address_ar', 'address_en',
            'facebook_url', 'instagram_url', 'tiktok_url', 'youtube_url',
            'currency_ar', 'currency_en', 'shipping_fee', 'free_shipping_threshold',
            'orders_enabled', 'reviews_auto_publish',
        ]
        widgets = {
            'about_ar': forms.Textarea(attrs={'rows': 6}),
            'about_en': forms.Textarea(attrs={'rows': 6}),
        }
        labels = {
            'brand_name_ar': 'اسم المتجر', 'brand_name_en': 'اسم المتجر',
            'tagline_ar': 'الشعار', 'tagline_en': 'الشعار',
            'logo': 'اللوجو (صورة — اختياري)', 'favicon': 'أيقونة التاب',
            'share_image': 'صورة المشاركة الافتراضية',
            'about_ar': 'من نحن', 'about_en': 'من نحن',
            'phone': 'رقم التليفون', 'whatsapp': 'واتساب', 'email': 'البريد الإلكتروني',
            'address_ar': 'العنوان', 'address_en': 'العنوان',
            'facebook_url': 'فيسبوك', 'instagram_url': 'إنستجرام', 'tiktok_url': 'تيك توك',
            'youtube_url': 'يوتيوب', 'currency_ar': 'العملة', 'currency_en': 'العملة',
            'shipping_fee': 'سعر الشحن العام', 'free_shipping_threshold': 'شحن مجاني فوق مبلغ (عام)',
            'orders_enabled': 'استقبال الطلبات',
            'reviews_auto_publish': 'نشر تقييمات العملاء تلقائيًا من غير مراجعة',
        }
        help_texts = {
            'share_image': 'بتظهر تحت أي رابط من الموقع لما يتبعت على واتساب/فيسبوك (1200×630 مثالي)',
        }


class PaymentSettingsForm(StyledForm):
    paypal_secret = forms.CharField(
        label='PayPal Secret', required=False,
        widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'new-password', 'dir': 'ltr'}),
        help_text='سيبه فاضي علشان يفضل المحفوظ زي ما هو',
    )

    class Meta:
        model = SiteSettings
        fields = [
            'paypal_enabled', 'paypal_link', 'paypal_rate', 'paypal_currency',
            'paypal_client_id', 'paypal_secret', 'paypal_sandbox', 'cod_enabled',
        ]
        labels = {
            'paypal_enabled': 'تفعيل الدفع عبر PayPal',
            'paypal_link': 'لينك الدفع (PayPal.me)',
            'paypal_rate': 'سعر الدولار بالجنيه',
            'paypal_currency': 'عملة PayPal',
            'paypal_client_id': 'PayPal Client ID',
            'paypal_sandbox': 'وضع التجربة (Sandbox) — للاختبار بس',
            'cod_enabled': 'تفعيل الدفع عند الاستلام',
        }
        help_texts = {
            'paypal_link': 'مثال: https://paypal.me/YourName — لو لينك PayPal.me المبلغ بيتضاف له أوتوماتيك',
            'paypal_rate': 'PayPal مش بيقبل الجنيه، فالمبلغ بيتقسم على الرقم ده — مثال: 50',
            'paypal_currency': 'غالبًا USD',
            'paypal_client_id': 'اختياري — مع الـ Secret بيظهر زرار PayPal الرسمي ويتأكد الدفع أوتوماتيك',
        }
        widgets = {
            'paypal_link': forms.URLInput(attrs={'dir': 'ltr', 'placeholder': 'https://paypal.me/YourName'}),
            'paypal_client_id': forms.TextInput(attrs={'dir': 'ltr'}),
            'paypal_currency': forms.TextInput(attrs={'dir': 'ltr', 'maxlength': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.paypal_secret:
            self.fields['paypal_secret'].widget.attrs['placeholder'] = '•••••••• (محفوظ)'

    def clean_paypal_currency(self):
        return (self.cleaned_data.get('paypal_currency') or 'USD').upper()[:3]

    def clean_paypal_rate(self):
        rate = self.cleaned_data.get('paypal_rate')
        if rate is None or rate <= 0:
            raise forms.ValidationError('اكتب سعر أكبر من صفر')
        return rate

    def clean(self):
        data = super().clean()
        if data.get('paypal_enabled') and not data.get('paypal_link') and not (
            data.get('paypal_client_id') and (data.get('paypal_secret') or self.instance.paypal_secret)
        ):
            raise forms.ValidationError('علشان تفعّل PayPal حط لينك الدفع أو Client ID + Secret')
        if not data.get('paypal_enabled') and not data.get('cod_enabled'):
            raise forms.ValidationError('لازم طريقة دفع واحدة على الأقل تكون مفعّلة')
        return data

    def save(self, commit=True):
        secret = self.cleaned_data.get('paypal_secret')
        obj = super().save(commit=False)
        if not secret:
            obj.paypal_secret = SiteSettings.objects.filter(pk=obj.pk).values_list(
                'paypal_secret', flat=True
            ).first() or ''
        if commit:
            obj.save()
        return obj


# ================================================================== portfolio
class WorkForm(StyledForm):
    class Meta:
        model = Work
        fields = [
            'title_ar', 'title_en', 'category', 'cover', 'summary_ar', 'summary_en',
            'description_ar', 'description_en', 'client', 'work_date',
            'is_active', 'is_featured', 'ordering', 'slug',
        ]
        widgets = {
            'work_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'summary_ar': forms.Textarea(attrs={'rows': 2}),
            'summary_en': forms.Textarea(attrs={'rows': 2}),
            'description_ar': forms.Textarea(attrs={'rows': 6}),
            'description_en': forms.Textarea(attrs={'rows': 6}),
        }
        labels = {
            'title_ar': 'اسم العمل', 'title_en': 'اسم العمل', 'category': 'التصنيف',
            'cover': 'البانر / صورة الغلاف',
            'summary_ar': 'نبذة قصيرة', 'summary_en': 'نبذة قصيرة',
            'description_ar': 'التفاصيل', 'description_en': 'التفاصيل',
            'client': 'العميل (اختياري)', 'work_date': 'التاريخ (اختياري)',
            'is_active': 'منشور في الموقع', 'is_featured': 'يظهر في الصفحة الرئيسية',
            'ordering': 'الترتيب', 'slug': 'الرابط (slug)',
        }
        help_texts = {
            'summary_ar': 'بتظهر في الكارت وتحت الرابط لما تشاركه',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False
        self.fields['category'].empty_label = '— بدون تصنيف —'
        self.fields['work_date'].input_formats = ['%Y-%m-%d']


class WorkCategoryForm(StyledForm):
    class Meta:
        model = WorkCategory
        fields = ['name_ar', 'name_en', 'ordering']
        labels = {'name_ar': 'اسم التصنيف', 'name_en': 'اسم التصنيف', 'ordering': 'الترتيب'}


# ==================================================================== reviews
class ReviewForm(StyledForm):
    class Meta:
        model = Review
        fields = ['name', 'rating', 'comment', 'reply', 'is_approved', 'is_featured']
        widgets = {
            'rating': forms.Select(choices=[(i, '★' * i) for i in range(5, 0, -1)]),
            'comment': forms.Textarea(attrs={'rows': 5}),
            'reply': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'name': 'اسم العميل الظاهر', 'rating': 'التقييم', 'comment': 'نص التقييم',
            'reply': 'رد المتجر (اختياري)', 'is_approved': 'منشور في الموقع',
            'is_featured': 'مميز — يظهر في الصفحة الرئيسية',
        }


class ReviewCreateForm(ReviewForm):
    """Adding a review by hand from the dashboard — it has to belong to a customer."""

    user = forms.ModelChoiceField(label='العميل', queryset=get_user_model().objects.none())
    order = forms.ModelChoiceField(
        label='الطلب (اختياري)', queryset=Order.objects.none(), required=False,
        help_text='لازم يكون من طلبات نفس العميل ومفيش عليه تقييم',
    )

    class Meta(ReviewForm.Meta):
        fields = ['user', 'order'] + ReviewForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        users = get_user_model().objects.filter(is_staff=False).order_by('first_name', 'username')
        self.fields['user'].queryset = users
        self.fields['user'].label_from_instance = (
            lambda u: f'{u.get_full_name() or u.username} — {u.email}' if u.email else (u.get_full_name() or u.username)
        )
        self.fields['order'].queryset = Order.objects.filter(review__isnull=True, user__isnull=False)
        self.fields['order'].label_from_instance = lambda o: f'{o.order_number} — {o.full_name}'
        self.fields['name'].required = False
        self.fields['name'].help_text = 'لو فاضي هيتكتب اسم العميل'
        for name in ('user', 'order'):
            self.fields[name].widget.attrs.setdefault('class', 'inp select')

    def clean(self):
        data = super().clean()
        user, order = data.get('user'), data.get('order')
        if user and order and order.user_id != user.pk:
            self.add_error('order', 'الطلب ده مش بتاع العميل اللي اخترته')
        if user and not data.get('name'):
            data['name'] = user.get_full_name() or user.username
        return data


class CustomerForm(forms.Form):
    """Add / edit a customer account (auth.User + CustomerProfile) from the dashboard."""

    full_name = forms.CharField(label='الاسم', max_length=150)
    email = forms.EmailField(label='البريد الإلكتروني', widget=forms.EmailInput(attrs={'dir': 'ltr'}))
    phone = forms.CharField(label='الموبايل', max_length=30, required=False,
                            widget=forms.TextInput(attrs={'dir': 'ltr'}))
    phone_alt = forms.CharField(label='موبايل آخر', max_length=30, required=False,
                                widget=forms.TextInput(attrs={'dir': 'ltr'}))
    country = forms.ModelChoiceField(label='الدولة', queryset=Country.objects.none(), required=False)
    city = forms.CharField(label='المدينة', max_length=120, required=False)
    address = forms.CharField(label='العنوان', required=False, widget=forms.Textarea(attrs={'rows': 3}))
    password = forms.CharField(
        label='كلمة المرور', required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'dir': 'ltr'}),
    )
    admin_note = forms.CharField(label='ملاحظة داخلية (مش بتظهر للعميل)', required=False,
                                 widget=forms.Textarea(attrs={'rows': 2}))
    is_active = forms.BooleanField(label='الحساب مفعّل', required=False, initial=True)

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        self.fields['country'].queryset = Country.objects.order_by('ordering', 'name_ar')
        self.fields['country'].label_from_instance = lambda c: c.name_ar
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'switch-input')
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'inp select')
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault('class', 'inp area')
            else:
                widget.attrs.setdefault('class', 'inp')
        if instance is None:
            self.fields['password'].help_text = (
                '8 حروف على الأقل — لو سبتها فاضية العميل يقدر يدخل بجوجل أو ديسكورد بنفس الإيميل'
            )
        else:
            self.fields['password'].help_text = 'اتركها فاضية علشان تفضل زي ما هي'

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        qs = get_user_model().objects.filter(email__iexact=email)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('الإيميل ده عليه حساب تاني')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password') or ''
        if password:
            if len(password) < 8:
                raise forms.ValidationError('كلمة المرور لازم تكون 8 حروف على الأقل')
            validate_password(password, self.instance)
        return password


class OrderEditForm(StyledForm):
    """Customer / delivery details of an order (items and payment stay as they are)."""

    class Meta:
        model = Order
        fields = [
            'full_name', 'phone', 'phone_alt', 'email', 'country', 'city', 'address',
            'notes', 'shipping_fee', 'admin_note',
        ]
        widgets = {
            'phone': forms.TextInput(attrs={'dir': 'ltr'}),
            'phone_alt': forms.TextInput(attrs={'dir': 'ltr'}),
            'email': forms.EmailInput(attrs={'dir': 'ltr'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'admin_note': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'full_name': 'اسم العميل', 'phone': 'الموبايل', 'phone_alt': 'موبايل آخر',
            'email': 'البريد الإلكتروني', 'country': 'الدولة', 'city': 'المدينة',
            'address': 'العنوان', 'notes': 'ملاحظات العميل', 'shipping_fee': 'سعر الشحن',
            'admin_note': 'ملاحظة داخلية',
        }
        help_texts = {
            'shipping_fee': 'الإجمالي بيتحسب تاني أوتوماتيك لو غيّرت سعر الشحن',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].queryset = Country.objects.order_by('ordering', 'name_ar')
        self.fields['country'].label_from_instance = lambda c: c.name_ar


# ============================================================= about / story
class AboutBlockForm(StyledForm):
    """The «حكايتنا» block on the homepage (its HomeSection row)."""

    class Meta:
        model = HomeSection
        fields = [
            'is_active', 'eyebrow_ar', 'eyebrow_en', 'title_ar', 'title_en',
            'subtitle_ar', 'subtitle_en', 'button_text_ar', 'button_text_en', 'button_link', 'image',
        ]
        widgets = {
            'title_ar': forms.Textarea(attrs={'rows': 2}),
            'title_en': forms.Textarea(attrs={'rows': 2}),
            'subtitle_ar': forms.Textarea(attrs={'rows': 4}),
            'subtitle_en': forms.Textarea(attrs={'rows': 4}),
            'button_link': forms.TextInput(attrs={'dir': 'ltr'}),
            'image': forms.FileInput(attrs={'class': 'inp file', 'accept': 'image/*'}),
        }
        labels = {
            'is_active': 'القسم ظاهر في الصفحة الرئيسية',
            'eyebrow_ar': 'الكلمة الصغيرة فوق العنوان', 'eyebrow_en': 'الكلمة الصغيرة فوق العنوان',
            'title_ar': 'العنوان', 'title_en': 'العنوان',
            'subtitle_ar': 'النص المختصر', 'subtitle_en': 'النص المختصر',
            'button_text_ar': 'نص الزرار', 'button_text_en': 'نص الزرار',
            'button_link': 'رابط الزرار', 'image': 'الصورة',
        }
        help_texts = {
            'subtitle_ar': 'لو فاضي هيظهر أول الحكاية الكاملة',
            'button_text_ar': 'سيبه فاضي لو مش عايز زرار',
            'image': 'لو مفيش صورة هيظهر اللوجو',
        }


class AboutStoryForm(StyledForm):
    class Meta:
        model = SiteSettings
        fields = ['about_ar', 'about_en']
        widgets = {
            'about_ar': forms.Textarea(attrs={'rows': 8}),
            'about_en': forms.Textarea(attrs={'rows': 8}),
        }
        labels = {'about_ar': 'الحكاية الكاملة', 'about_en': 'الحكاية الكاملة'}
        help_texts = {'about_ar': 'بتظهر في صفحة «من نحن» — كل سطر جديد بيبقى فقرة'}


class AboutPageForm(StyledForm):
    class Meta:
        model = AboutPage
        fields = [
            'tag_ar', 'tag_en', 'show_tag', 'stats_mode', 'stats_on_home', 'stats_on_page',
            'page_title_ar', 'page_title_en', 'page_subtitle_ar', 'page_subtitle_en', 'page_image',
            'button1_text_ar', 'button1_text_en', 'button1_link',
            'button2_text_ar', 'button2_text_en', 'button2_link',
        ]
        widgets = {
            'stats_mode': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'page_image': forms.FileInput(attrs={'class': 'inp file', 'accept': 'image/*'}),
            'button1_link': forms.TextInput(attrs={'dir': 'ltr'}),
            'button2_link': forms.TextInput(attrs={'dir': 'ltr'}),
        }
        labels = {
            'tag_ar': 'الكلمة اللي على الصورة', 'tag_en': 'الكلمة اللي على الصورة',
            'show_tag': 'إظهار الكلمة اللي على الصورة',
            'stats_mode': 'الأرقام', 'stats_on_home': 'الأرقام تظهر في الصفحة الرئيسية',
            'stats_on_page': 'الأرقام تظهر في صفحة «من نحن»',
            'page_title_ar': 'عنوان الصفحة', 'page_title_en': 'عنوان الصفحة',
            'page_subtitle_ar': 'السطر تحت العنوان', 'page_subtitle_en': 'السطر تحت العنوان',
            'page_image': 'صورة الصفحة',
            'button1_text_ar': 'الزرار الأول', 'button1_text_en': 'الزرار الأول', 'button1_link': 'رابط الزرار الأول',
            'button2_text_ar': 'الزرار التاني', 'button2_text_en': 'الزرار التاني', 'button2_link': 'رابط الزرار التاني',
        }
        help_texts = {
            'tag_ar': 'لو فاضية هيظهر اسم المتجر',
            'page_title_ar': 'لو فاضي: «من نحن»',
            'page_subtitle_ar': 'لو فاضي هيظهر شعار المتجر',
            'page_image': 'لو فاضية هتظهر نفس صورة قسم الصفحة الرئيسية',
            'button1_text_ar': 'سيب النص فاضي علشان الزرار يختفي',
        }


class AboutStatForm(StyledForm):
    class Meta:
        model = AboutStat
        fields = ['value', 'suffix', 'show_star', 'label_ar', 'label_en', 'is_active', 'ordering']
        widgets = {
            'value': forms.TextInput(attrs={'dir': 'ltr', 'placeholder': '500'}),
            'suffix': forms.TextInput(attrs={'dir': 'ltr', 'placeholder': '+'}),
        }
        labels = {
            'value': 'الرقم', 'suffix': 'علامة بعد الرقم', 'show_star': 'نجمة جنب الرقم',
            'label_ar': 'الوصف', 'label_en': 'الوصف', 'is_active': 'ظاهر', 'ordering': 'الترتيب',
        }
        help_texts = {'label_ar': 'مثلاً: عميل سعيد'}


# ============================================================= homepage / nav
class HomeSectionForm(StyledForm):
    class Meta:
        model = HomeSection
        fields = [
            'is_active', 'eyebrow_ar', 'eyebrow_en', 'title_ar', 'title_en',
            'subtitle_ar', 'subtitle_en', 'button_text_ar', 'button_text_en',
            'button_link', 'image', 'image_mobile', 'image_focus', 'image_focus_mobile',
            'script_text', 'items_limit',
        ]
        widgets = {
            'image_focus': forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 100, 'step': 1, 'class': 'inp range'}),
            'image_focus_mobile': forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 100, 'step': 1, 'class': 'inp range'}),
            'script_text': forms.Textarea(attrs={'rows': 4, 'dir': 'ltr'}),
            'title_ar': forms.Textarea(attrs={'rows': 2}),
            'title_en': forms.Textarea(attrs={'rows': 2}),
            'subtitle_ar': forms.Textarea(attrs={'rows': 3}),
            'subtitle_en': forms.Textarea(attrs={'rows': 3}),
            'button_link': forms.TextInput(attrs={'dir': 'ltr'}),
        }
        labels = {
            'is_active': 'ظاهر في الصفحة الرئيسية',
            'eyebrow_ar': 'الكلمة الصغيرة فوق العنوان', 'eyebrow_en': 'الكلمة الصغيرة فوق العنوان',
            'title_ar': 'العنوان', 'title_en': 'العنوان',
            'subtitle_ar': 'النص', 'subtitle_en': 'النص',
            'button_text_ar': 'نص الزرار', 'button_text_en': 'نص الزرار',
            'button_link': 'رابط الزرار', 'image': 'صورة', 'items_limit': 'عدد العناصر المعروضة',
            'image_mobile': 'صورة للموبايل (اختياري)',
            'image_focus': 'مكان الصورة على الكمبيوتر (شمال ← يمين)',
            'image_focus_mobile': 'مكان الصورة على الموبايل (شمال ← يمين)',
            'script_text': 'الكلام المكتوب بخط اليد (على الشاشات الكبيرة)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        section = self.instance
        if not section.uses_image:
            self.fields.pop('image', None)
        else:
            self.fields['image'].help_text = (
                'صورة خلفية الواجهة — لو فاضية هتفضل الصورة الحالية'
                if section.key == 'hero' else 'صورة جنب نص «من نحن»'
            )
        if not section.uses_limit:
            self.fields.pop('items_limit', None)
        if section.key == 'hero':
            self.fields['image_mobile'].help_text = 'لو فاضية الموبايل هيعرض نفس الصورة — الأفضل صورة طولية أو مربعة'
            self.fields['image_focus'].help_text = 'حرّك علشان تختار أنهي جزء من الصورة يبان'
            self.fields['script_text'].help_text = 'كل كلمة في سطر — سيبه فاضي للكلام الافتراضي'
            self.fields['title_en'].help_text = 'اكتب السطر الأول، Enter، وبعدين السطر التاني (بيتلوّن)'
            for name, default in (('image_focus', 58), ('image_focus_mobile', 40)):
                self.fields[name].required = False
                if getattr(section, name) is None:
                    self.initial[name] = default
        else:
            for name in ('image_mobile', 'image_focus', 'image_focus_mobile', 'script_text'):
                self.fields.pop(name, None)
        if section.key in ('banners', 'features'):
            for name in list(self.fields):
                if name != 'is_active':
                    self.fields.pop(name)
        if section.key == 'about':
            self.fields['subtitle_ar'].help_text = 'لو فاضي هيظهر نص «من نحن» من إعدادات المتجر'
        if section.key == 'hero':
            # the hero is English in both languages → only the English texts are edited
            for name in ('eyebrow_ar', 'title_ar', 'subtitle_ar', 'button_text_ar'):
                self.fields.pop(name, None)
            for name in ('eyebrow_en', 'title_en', 'subtitle_en', 'button_text_en'):
                self.fields[name].help_text = ''
            self.fields['title_en'].help_text = 'سطرين: السطر التاني (بعد Enter) بيظهر ملوّن — مثال: DESIGN YOUR ↵ IDENTITY'


class NavLinkForm(StyledForm):
    class Meta:
        model = NavLink
        fields = ['link_type', 'category', 'policy', 'url', 'label_ar', 'label_en', 'new_tab', 'is_active']
        widgets = {'url': forms.TextInput(attrs={'dir': 'ltr', 'placeholder': 'https://… أو /shop/'})}
        labels = {
            'link_type': 'نوع الرابط', 'category': 'القسم', 'policy': 'السياسة',
            'url': 'الرابط', 'label_ar': 'الاسم الظاهر', 'label_en': 'الاسم الظاهر',
            'new_tab': 'يفتح في تاب جديد', 'is_active': 'ظاهر في القائمة',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = '—'
        self.fields['policy'].empty_label = '—'
        self.fields['label_ar'].help_text = 'اتركه فاضي علشان ياخد الاسم الافتراضي'
        self.fields['label_en'].help_text = 'اتركه فاضي علشان ياخد الاسم الافتراضي'

    def clean(self):
        data = super().clean()
        kind = data.get('link_type')
        if kind == 'category' and not data.get('category'):
            self.add_error('category', 'اختار القسم')
        if kind == 'policy' and not data.get('policy'):
            self.add_error('policy', 'اختار السياسة')
        if kind == 'custom':
            if not data.get('url'):
                self.add_error('url', 'اكتب الرابط')
            if not (data.get('label_ar') or data.get('label_en')):
                self.add_error('label_ar', 'اكتب اسم للرابط')
        return data


class PolicyForm(StyledForm):
    class Meta:
        model = Policy
        fields = [
            'title_ar', 'title_en', 'content_ar', 'content_en',
            'is_active', 'show_in_footer', 'ordering', 'slug',
        ]
        widgets = {
            'content_ar': forms.Textarea(attrs={'rows': 16}),
            'content_en': forms.Textarea(attrs={'rows': 16}),
        }
        labels = {
            'title_ar': 'عنوان السياسة', 'title_en': 'عنوان السياسة',
            'content_ar': 'المحتوى', 'content_en': 'المحتوى',
            'is_active': 'منشورة', 'show_in_footer': 'تظهر في الفوتر',
            'ordering': 'الترتيب', 'slug': 'الرابط (slug)',
        }
        help_texts = {
            'content_ar': 'اكتب عادي — كل سطر جديد بيظهر في سطر لوحده، والسطر اللي يبدأ بـ # بيبقى عنوان',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False


# ====================================================================== staff
class StaffForm(forms.Form):
    full_name = forms.CharField(label='الاسم', max_length=150)
    username = forms.CharField(
        label='اسم المستخدم (للدخول)', max_length=150,
        widget=forms.TextInput(attrs={'dir': 'ltr', 'autocomplete': 'off'}),
    )
    email = forms.EmailField(label='البريد الإلكتروني', required=False,
                             widget=forms.EmailInput(attrs={'dir': 'ltr'}))
    job_title = forms.CharField(label='المسمى الوظيفي (اختياري)', max_length=80, required=False)
    password = forms.CharField(
        label='كلمة المرور', required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'dir': 'ltr'}),
    )
    permissions = forms.MultipleChoiceField(
        label='الصلاحيات', choices=STAFF_PERMISSIONS, required=False,
        widget=forms.CheckboxSelectMultiple(),
    )
    is_active = forms.BooleanField(label='الحساب مفعّل', required=False, initial=True)

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'switch-input')
            elif not isinstance(widget, forms.CheckboxSelectMultiple):
                widget.attrs.setdefault('class', 'inp')
        if instance is None:
            self.fields['password'].required = True
            self.fields['password'].help_text = '8 حروف على الأقل'
        else:
            self.fields['password'].help_text = 'اتركها فاضية علشان تفضل زي ما هي'

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        qs = get_user_model().objects.filter(username__iexact=username)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('اسم المستخدم ده مستخدم قبل كده')
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password') or ''
        if password:
            if len(password) < 8:
                raise forms.ValidationError('كلمة المرور لازم تكون 8 حروف على الأقل')
            validate_password(password, self.instance)
        return password
