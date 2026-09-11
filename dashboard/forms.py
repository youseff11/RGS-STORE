"""Dashboard forms.

The storefront is English-only, so the forms expose the English fields.
The `*_ar` columns stay in the database and are mirrored from the English
value on save, which keeps the Django admin and any legacy rows consistent.
"""

from django import forms

from .models import (
    Announcement, Banner, Category, Coupon, Governorate, Product, ProductColor,
    Promotion, SiteSettings, Size,
)

DATETIME_FORMATS = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']


class StyledForm(forms.ModelForm):
    """Attaches the dashboard CSS classes to every widget."""

    #: {english_field: arabic_field} copied across on save
    MIRROR = {}
    #: fields the model marks optional but the dashboard must require
    REQUIRED = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.REQUIRED:
            if name in self.fields:
                self.fields[name].required = True
        for field in self.fields.values():
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

    def save(self, commit=True):
        obj = super().save(commit=False)
        for source, target in self.MIRROR.items():
            setattr(obj, target, getattr(obj, source, '') or '')
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class ProductForm(StyledForm):
    MIRROR = {'name_en': 'name_ar', 'short_en': 'short_ar',
              'description_en': 'description_ar'}
    REQUIRED = ('name_en',)

    class Meta:
        model = Product
        fields = [
            'name_en', 'category', 'sku', 'price', 'compare_price',
            'short_en', 'description_en',
            'is_active', 'is_featured', 'is_new', 'ordering', 'slug',
        ]
        widgets = {'description_en': forms.Textarea(attrs={'rows': 5})}
        labels = {
            'name_en': 'اسم المنتج', 'category': 'القسم', 'sku': 'كود المنتج (SKU)',
            'price': 'السعر', 'compare_price': 'السعر قبل الخصم (اختياري)',
            'short_en': 'وصف مختصر', 'description_en': 'الوصف الكامل',
            'is_active': 'معروض في المتجر', 'is_featured': 'منتج مميز',
            'is_new': 'علامة «جديد»', 'ordering': 'ترتيب الظهور', 'slug': 'الرابط (slug)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = '— بدون قسم —'


class CategoryForm(StyledForm):
    MIRROR = {'name_en': 'name_ar', 'description_en': 'description_ar'}
    REQUIRED = ('name_en',)

    class Meta:
        model = Category
        fields = [
            'name_en', 'slug', 'description_en',
            'image', 'is_active', 'is_featured', 'ordering',
        ]
        labels = {
            'name_en': 'اسم القسم', 'slug': 'الرابط (slug)', 'description_en': 'الوصف',
            'image': 'صورة القسم', 'is_active': 'مفعّل',
            'is_featured': 'يظهر في الصفحة الرئيسية', 'ordering': 'الترتيب',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False


class ColorForm(StyledForm):
    MIRROR = {'name_en': 'name_ar'}
    REQUIRED = ('name_en',)

    class Meta:
        model = ProductColor
        fields = ['name_en', 'hex_code']
        widgets = {'hex_code': forms.TextInput(attrs={'type': 'color'})}
        labels = {'name_en': 'اسم اللون', 'hex_code': 'الكود اللوني'}


class SizeForm(StyledForm):
    class Meta:
        model = Size
        fields = ['name', 'ordering']
        labels = {'name': 'المقاس', 'ordering': 'الترتيب'}


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
    MIRROR = {'badge_en': 'badge_ar'}

    class Meta:
        model = Promotion
        fields = [
            'title', 'scope', 'discount_type', 'value', 'categories', 'products',
            'badge_en', 'start_at', 'end_at', 'is_active',
        ]
        widgets = {
            'categories': forms.CheckboxSelectMultiple(),
            'products': forms.SelectMultiple(attrs={'size': 10}),
            'start_at': forms.DateTimeInput(),
            'end_at': forms.DateTimeInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['products'].queryset = Product.objects.all()
        for name in ('start_at', 'end_at'):
            self.fields[name].input_formats = DATETIME_FORMATS


class AnnouncementForm(StyledForm):
    MIRROR = {'text_en': 'text_ar'}
    REQUIRED = ('text_en',)

    class Meta:
        model = Announcement
        fields = ['text_en', 'link', 'is_active', 'ordering']
        labels = {
            'text_en': 'نص الإعلان', 'link': 'رابط (اختياري)',
            'is_active': 'ظاهر في الشريط', 'ordering': 'الترتيب',
        }


class BannerForm(StyledForm):
    MIRROR = {'title_en': 'title_ar', 'subtitle_en': 'subtitle_ar',
              'button_text_en': 'button_text_ar'}

    class Meta:
        model = Banner
        fields = [
            'title_en', 'subtitle_en', 'button_text_en',
            'link', 'image', 'is_active', 'ordering',
        ]
        labels = {
            'title_en': 'العنوان', 'subtitle_en': 'العنوان الفرعي',
            'button_text_en': 'نص الزرار', 'link': 'الرابط',
            'image': 'الصورة', 'is_active': 'ظاهر', 'ordering': 'الترتيب',
        }


class GovernorateForm(StyledForm):
    MIRROR = {'name_en': 'name_ar'}
    REQUIRED = ('name_en',)

    class Meta:
        model = Governorate
        fields = ['name_en', 'shipping_fee', 'is_active', 'ordering']
        labels = {
            'name_en': 'اسم المحافظة', 'shipping_fee': 'سعر شحن خاص (اختياري)',
            'is_active': 'متاحة', 'ordering': 'الترتيب',
        }


class SiteSettingsForm(StyledForm):
    MIRROR = {'brand_name_en': 'brand_name_ar', 'tagline_en': 'tagline_ar',
              'about_en': 'about_ar', 'address_en': 'address_ar'}
    REQUIRED = ('brand_name_en',)

    class Meta:
        model = SiteSettings
        fields = [
            'brand_name_en', 'tagline_en', 'logo', 'favicon', 'about_en',
            'phone', 'whatsapp', 'email', 'address_en',
            'facebook_url', 'instagram_url', 'tiktok_url', 'youtube_url',
            'currency_en', 'shipping_fee', 'free_shipping_threshold',
            'low_stock_threshold', 'orders_enabled',
        ]
        widgets = {'about_en': forms.Textarea(attrs={'rows': 5})}
