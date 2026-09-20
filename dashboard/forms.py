"""Dashboard forms.

The storefront is Arabic by default with an English switch, so every
translatable field comes in a pair: `<name>_ar` (required where the model
requires it) and `<name>_en` (optional — the site falls back to Arabic).
`dashboard/_form_fields.html` renders each pair side by side.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import (
    Announcement, Banner, Category, Country, Coupon, HomeSection, NavLink, Policy,
    Product, ProductColor, Promotion, Review, STAFF_PERMISSIONS, SiteSettings, Size,
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


class SizeForm(StyledForm):
    class Meta:
        model = Size
        fields = ['name', 'ordering']
        labels = {'name': 'المقاس', 'ordering': 'الترتيب'}


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

# =================================================================== settings
class SiteSettingsForm(StyledForm):
    REQUIRED = ('brand_name_ar',)

    class Meta:
        model = SiteSettings
        fields = [
            'brand_name_ar', 'brand_name_en', 'tagline_ar', 'tagline_en',
            'logo', 'favicon', 'share_image', 'about_ar', 'about_en',
            'phone', 'whatsapp', 'email', 'address_ar', 'address_en',
            'facebook_url', 'instagram_url', 'tiktok_url', 'youtube_url',
            'currency_ar', 'currency_en', 'shipping_fee', 'free_shipping_threshold',
            'low_stock_threshold', 'orders_enabled', 'reviews_auto_publish',
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
            'low_stock_threshold': 'تنبيه المخزون القليل عند', 'orders_enabled': 'استقبال الطلبات',
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


# ============================================================= homepage / nav
class HomeSectionForm(StyledForm):
    class Meta:
        model = HomeSection
        fields = [
            'is_active', 'eyebrow_ar', 'eyebrow_en', 'title_ar', 'title_en',
            'subtitle_ar', 'subtitle_en', 'button_text_ar', 'button_text_en',
            'button_link', 'image', 'items_limit',
        ]
        widgets = {
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
            self.fields['title_en'].help_text = 'سطرين: السطر التاني (بعد Enter) بيظهر ملوّن — مثال: WEAR YOUR ↵ CONFIDENCE'


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
