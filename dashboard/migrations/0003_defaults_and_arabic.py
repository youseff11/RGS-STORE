"""Default homepage sections, navbar and policy pages + Arabic names.

While the store was English-only, the Arabic columns were filled with a copy
of the English text. Arabic is the default language again, so rows that still
carry that copy get their real Arabic name here (only when both columns are
identical — anything the owner already edited is left alone).
"""

from django.db import migrations

GOVERNORATES_AR = {
    'Cairo': 'القاهرة', 'Giza': 'الجيزة', 'Alexandria': 'الإسكندرية', 'Qalyubia': 'القليوبية',
    'Dakahlia': 'الدقهلية', 'Sharqia': 'الشرقية', 'Gharbia': 'الغربية', 'Monufia': 'المنوفية',
    'Beheira': 'البحيرة', 'Kafr El Sheikh': 'كفر الشيخ', 'Damietta': 'دمياط',
    'Port Said': 'بورسعيد', 'Ismailia': 'الإسماعيلية', 'Suez': 'السويس',
    'North Sinai': 'شمال سيناء', 'South Sinai': 'جنوب سيناء', 'Beni Suef': 'بني سويف',
    'Fayoum': 'الفيوم', 'Minya': 'المنيا', 'Asyut': 'أسيوط', 'Sohag': 'سوهاج', 'Qena': 'قنا',
    'Luxor': 'الأقصر', 'Aswan': 'أسوان', 'Red Sea': 'البحر الأحمر', 'New Valley': 'الوادي الجديد',
    'Matrouh': 'مطروح',
}

CATEGORIES_AR = {
    'T-Shirts': 'تيشيرتات', 'Shirts': 'قمصان', 'Pants': 'بناطيل', 'Jackets': 'جواكت',
    'Shoes': 'أحذية', 'Accessories': 'إكسسوارات',
}

SECTIONS = [
    ('hero', 'موسم جديد', 'NEW SEASON', 'البس\nثقتك', 'WEAR YOUR\nCONFIDENCE',
     'خامات ممتازة. ستايلات مودرن. معمولة عشانك.', 'Premium quality. Modern styles. Made for you.',
     'تسوّق الآن', 'SHOP NOW', '/shop/', 8),
    ('banners', '', '', '', '', '', '', '', '', '', 8),
    ('features', '', '', '', '', '', '', '', '', '', 4),
    ('categories', 'الأقسام', 'Categories', 'تصفح الأقسام', 'Browse categories',
     'اختار القسم اللي يناسب ستايلك', 'Pick the section that fits your style', '', '', '', 6),
    ('featured', 'مختارات', 'Featured', 'منتجات مختارة', 'Featured pieces',
     'قطع اخترناها لك من أحدث المجموعات', 'Hand-picked pieces from our latest drops',
     'عرض الكل', 'View all', '/shop/', 8),
    ('about', 'من نحن', 'About us', 'حكايتنا', 'Our story', '', '',
     'اعرف أكتر', 'Learn more', '/about/', 8),
    ('portfolio', 'أعمالنا', 'Our work', 'من أعمالنا', 'Selected work',
     'لقطات من شغلنا — صور وفيديوهات', 'Moments from our work — photos and films',
     'كل الأعمال', 'All work', '/works/', 5),
    ('sale', 'العروض', 'Sale', 'عروض لفترة محدودة', 'Limited-time offers', '', '',
     'عرض الكل', 'View all', '/shop/?sale=1', 8),
    ('new_arrivals', 'جديد', 'New', 'وصل حديثًا', 'New arrivals',
     'آخر ما وصل إلى المتجر', 'The latest to land in store', 'عرض الكل', 'View all', '/shop/?sort=new', 8),
    ('reviews', 'تقييمات العملاء', 'Reviews', 'آراء عملائنا', 'What our customers say',
     'تقييمات حقيقية من عملاء اشتروا من المتجر', 'Real ratings from verified buyers',
     'كل التقييمات', 'All reviews', '/reviews/', 6),
]

NAV = ['home', 'shop', 'portfolio', 'sale', 'reviews', 'about', 'contact']

POLICIES = [
    ('سياسة الخصوصية', 'Privacy policy', 'privacy-policy'),
    ('سياسة الاستبدال والاسترجاع', 'Returns & exchanges', 'returns-policy'),
    ('سياسة الشحن والتوصيل', 'Shipping policy', 'shipping-policy'),
    ('الشروط والأحكام', 'Terms & conditions', 'terms'),
]


def forwards(apps, schema_editor):
    HomeSection = apps.get_model('dashboard', 'HomeSection')
    NavLink = apps.get_model('dashboard', 'NavLink')
    Policy = apps.get_model('dashboard', 'Policy')
    Governorate = apps.get_model('dashboard', 'Governorate')
    Category = apps.get_model('dashboard', 'Category')
    SiteSettings = apps.get_model('dashboard', 'SiteSettings')
    Announcement = apps.get_model('dashboard', 'Announcement')
    Order = apps.get_model('dashboard', 'Order')

    for index, row in enumerate(SECTIONS):
        key, eb_ar, eb_en, t_ar, t_en, s_ar, s_en, b_ar, b_en, link, limit = row
        HomeSection.objects.get_or_create(key=key, defaults=dict(
            ordering=index, eyebrow_ar=eb_ar, eyebrow_en=eb_en, title_ar=t_ar, title_en=t_en,
            subtitle_ar=s_ar, subtitle_en=s_en, button_text_ar=b_ar, button_text_en=b_en,
            button_link=link, items_limit=limit,
        ))

    if not NavLink.objects.exists():
        for index, key in enumerate(NAV):
            NavLink.objects.create(link_type=key, ordering=index)

    if not Policy.objects.exists():
        for index, (ar, en, slug) in enumerate(POLICIES):
            Policy.objects.create(title_ar=ar, title_en=en, slug=slug, ordering=index)

    for gov in Governorate.objects.all():
        if gov.name_ar == gov.name_en and gov.name_en in GOVERNORATES_AR:
            gov.name_ar = GOVERNORATES_AR[gov.name_en]
            gov.save(update_fields=['name_ar'])

    for cat in Category.objects.all():
        if cat.name_ar == cat.name_en and cat.name_en in CATEGORIES_AR:
            cat.name_ar = CATEGORIES_AR[cat.name_en]
            cat.save(update_fields=['name_ar'])

    site = SiteSettings.objects.filter(pk=1).first()
    if site:
        changed = []
        if site.tagline_ar == site.tagline_en == 'Menswear, refined.':
            site.tagline_ar = 'أناقة الرجل الحقيقي'
            changed.append('tagline_ar')
        if not site.currency_ar or site.currency_ar == site.currency_en:
            site.currency_ar = 'ج.م'
            changed.append('currency_ar')
        if changed:
            site.save(update_fields=changed)

    seed_text = 'Free shipping over 2000 EGP  •  Cash on delivery'
    Announcement.objects.filter(text_ar=seed_text, text_en=seed_text).update(
        text_ar='شحن مجاني للطلبات فوق 2000 ج.م  •  الدفع عند الاستلام أو PayPal'
    )

    # cash orders that were already delivered count as paid
    Order.objects.filter(status='delivered').update(payment_status='paid')


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_accounts_payments_portfolio_reviews'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
