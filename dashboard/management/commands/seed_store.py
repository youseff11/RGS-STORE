"""Seed the store with sensible defaults: settings, governorates, sizes, categories."""

from decimal import Decimal

from django.core.management.base import BaseCommand

from dashboard.models import Announcement, Category, Governorate, SiteSettings, Size

GOVERNORATES = [
    'Cairo', 'Giza', 'Alexandria', 'Qalyubia', 'Dakahlia', 'Sharqia', 'Gharbia',
    'Monufia', 'Beheira', 'Kafr El Sheikh', 'Damietta', 'Port Said', 'Ismailia',
    'Suez', 'North Sinai', 'South Sinai', 'Beni Suef', 'Fayoum', 'Minya',
    'Asyut', 'Sohag', 'Qena', 'Luxor', 'Aswan', 'Red Sea', 'New Valley', 'Matrouh',
]

SIZES = ['S', 'M', 'L', 'XL', '2XL', '3XL']

CATEGORIES = ['T-Shirts', 'Shirts', 'Pants', 'Jackets', 'Shoes', 'Accessories']


class Command(BaseCommand):
    help = 'Seed RGS TOWER with default settings, governorates, sizes and categories.'

    def handle(self, *args, **options):
        site = SiteSettings.load()
        site.brand_name_en = site.brand_name_en or 'RGS TOWER'
        site.brand_name_ar = site.brand_name_en
        site.tagline_en = site.tagline_en or 'Menswear, refined.'
        site.tagline_ar = site.tagline_en
        site.currency_en = site.currency_en or 'EGP'
        site.shipping_fee = site.shipping_fee or Decimal('60.00')
        site.save()
        self.stdout.write(self.style.SUCCESS('OK  site settings'))

        for index, name in enumerate(GOVERNORATES):
            Governorate.objects.get_or_create(
                name_en=name, defaults={'name_ar': name, 'ordering': index}
            )
        self.stdout.write(self.style.SUCCESS(f'OK  {len(GOVERNORATES)} governorates'))

        for index, name in enumerate(SIZES):
            Size.objects.get_or_create(name=name, defaults={'ordering': index})
        self.stdout.write(self.style.SUCCESS(f'OK  {len(SIZES)} sizes'))

        for index, name in enumerate(CATEGORIES):
            Category.objects.get_or_create(
                name_en=name, defaults={'name_ar': name, 'ordering': index}
            )
        self.stdout.write(self.style.SUCCESS(f'OK  {len(CATEGORIES)} categories'))

        if not Announcement.objects.exists():
            text = 'Free shipping over 2000 EGP  •  Cash on delivery'
            Announcement.objects.create(text_en=text, text_ar=text)
            self.stdout.write(self.style.SUCCESS('OK  announcement bar'))

        self.stdout.write(self.style.SUCCESS('\nRGS TOWER seeded successfully.'))
