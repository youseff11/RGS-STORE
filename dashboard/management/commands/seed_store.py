"""Seed the store with sensible defaults: settings, countries, sizes, categories."""

from decimal import Decimal

from django.core.management.base import BaseCommand

from dashboard.countries_data import COUNTRIES
from dashboard.models import (
    Announcement, Category, Country, HomeSection, NavLink, SiteSettings, Size,
    ensure_policy_defaults,
)

CATEGORIES_AR = {
    'T-Shirts': 'تيشيرتات', 'Shirts': 'قمصان', 'Pants': 'بناطيل', 'Jackets': 'جواكت',
    'Shoes': 'أحذية', 'Accessories': 'إكسسوارات',
}

SIZES = ['S', 'M', 'L', 'XL', '2XL', '3XL']

CATEGORIES = ['T-Shirts', 'Shirts', 'Pants', 'Jackets', 'Shoes', 'Accessories']


class Command(BaseCommand):
    help = 'Seed RGS TOWER with default settings, countries, sizes and categories.'

    def handle(self, *args, **options):
        site = SiteSettings.load()
        site.brand_name_en = site.brand_name_en or 'RGS TOWER'
        site.brand_name_ar = site.brand_name_ar or site.brand_name_en
        site.tagline_en = site.tagline_en or 'Menswear, refined.'
        site.tagline_ar = site.tagline_ar or 'أناقة الرجل الحقيقي'
        site.currency_en = site.currency_en or 'EGP'
        site.currency_ar = site.currency_ar or 'ج.م'
        site.shipping_fee = site.shipping_fee or Decimal('60.00')
        site.save()
        self.stdout.write(self.style.SUCCESS('OK  site settings'))

        # every country, switched off except Egypt — the rest are opened from the dashboard
        known = set(Country.objects.exclude(code='').values_list('code', flat=True))
        new = [
            Country(code=code, name_ar=name_ar, name_en=name_en, is_active=(code == 'EG'))
            for code, name_ar, name_en in COUNTRIES if code not in known
        ]
        Country.objects.bulk_create(new)
        self.stdout.write(self.style.SUCCESS(f'OK  {len(new)} countries added ({len(known)} already there)'))

        for index, name in enumerate(SIZES):
            Size.objects.get_or_create(name=name, defaults={'ordering': index})
        self.stdout.write(self.style.SUCCESS(f'OK  {len(SIZES)} sizes'))

        for index, name in enumerate(CATEGORIES):
            Category.objects.get_or_create(
                name_en=name, defaults={'name_ar': CATEGORIES_AR.get(name, name), 'ordering': index}
            )
        self.stdout.write(self.style.SUCCESS(f'OK  {len(CATEGORIES)} categories'))

        if not Announcement.objects.exists():
            Announcement.objects.create(
                text_ar='شحن مجاني للطلبات فوق 2000 ج.م  •  الدفع عند الاستلام أو PayPal',
                text_en='Free shipping over 2000 EGP  •  Cash on delivery or PayPal',
            )
            self.stdout.write(self.style.SUCCESS('OK  announcement bar'))

        HomeSection.ensure_defaults()
        NavLink.ensure_defaults()
        ensure_policy_defaults()
        self.stdout.write(self.style.SUCCESS('OK  homepage sections, navbar, policies'))

        self.stdout.write(self.style.SUCCESS('\nRGS TOWER seeded successfully.'))
