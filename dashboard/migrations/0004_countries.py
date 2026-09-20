"""Shipping by country instead of Egyptian governorate.

The store now exports, so «المحافظات» became «الدول»:

* `Governorate` → `Country` (Order.country / CustomerProfile.country), plus ISO code,
  a per-country free-shipping threshold and an optional delivery-time note.
* The full list of countries is loaded (Arabic + English). Egypt is on, everything
  else is off until it is switched on from the dashboard.
* The old governorate rows go away. Orders / customers that pointed at a governorate
  move to Egypt and keep the governorate name in their city field, so nothing is lost.
  Rows the owner added himself (not an Egyptian governorate) are matched to a country
  by name, or kept as they are.
"""

from django.db import migrations, models

from dashboard.countries_data import COUNTRIES

EGYPT_GOVERNORATES = {
    'Cairo', 'Giza', 'Alexandria', 'Qalyubia', 'Dakahlia', 'Sharqia', 'Gharbia', 'Monufia',
    'Beheira', 'Kafr El Sheikh', 'Damietta', 'Port Said', 'Ismailia', 'Suez', 'North Sinai',
    'South Sinai', 'Beni Suef', 'Fayoum', 'Minya', 'Asyut', 'Sohag', 'Qena', 'Luxor', 'Aswan',
    'Red Sea', 'New Valley', 'Matrouh',
    'القاهرة', 'الجيزة', 'الإسكندرية', 'القليوبية', 'الدقهلية', 'الشرقية', 'الغربية', 'المنوفية',
    'البحيرة', 'كفر الشيخ', 'دمياط', 'بورسعيد', 'الإسماعيلية', 'السويس', 'شمال سيناء',
    'جنوب سيناء', 'بني سويف', 'الفيوم', 'المنيا', 'أسيوط', 'سوهاج', 'قنا', 'الأقصر', 'أسوان',
    'البحر الأحمر', 'الوادي الجديد', 'مطروح',
}


def _norm(text):
    return (text or '').strip().lower()


def _with_region(region, city):
    city = (city or '').strip()
    if not region or region in city:
        return city
    return (f'{region} — {city}' if city else region)[:120]


def forwards(apps, schema_editor):
    Country = apps.get_model('dashboard', 'Country')
    Order = apps.get_model('dashboard', 'Order')
    CustomerProfile = apps.get_model('dashboard', 'CustomerProfile')

    old_rows = list(Country.objects.all())

    # 1) the list of countries (skip any code that is already there)
    existing = set(Country.objects.exclude(code='').values_list('code', flat=True))
    Country.objects.bulk_create([
        Country(code=code, name_ar=ar, name_en=en, is_active=(code == 'EG'), ordering=100)
        for code, ar, en in COUNTRIES if code not in existing
    ])
    by_code = {c.code: c for c in Country.objects.exclude(code='')}
    by_name = {}
    for c in by_code.values():
        by_name[_norm(c.name_ar)] = c
        by_name[_norm(c.name_en)] = c
    egypt = by_code['EG']

    # 2) what to do with each old governorate row
    for row in old_rows:
        names = {row.name_ar.strip(), (row.name_en or '').strip()}
        if names & EGYPT_GOVERNORATES:
            target, region = egypt, row.name_ar or row.name_en
        else:
            target = by_name.get(_norm(row.name_ar)) or by_name.get(_norm(row.name_en))
            region = ''
            if target is None:
                continue  # a custom row the owner added — keep it as a country
            # the owner already set this one up as a country: keep his settings
            target.is_active = row.is_active
            if row.shipping_fee is not None:
                target.shipping_fee = row.shipping_fee
            target.save(update_fields=['is_active', 'shipping_fee'])

        for order in Order.objects.filter(country=row):
            order.city = _with_region(region, order.city)
            order.country = target
            order.save(update_fields=['city', 'country'])
        for profile in CustomerProfile.objects.filter(country=row):
            profile.city = _with_region(region, profile.city)
            profile.country = target
            profile.save(update_fields=['city', 'country'])
        row.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_defaults_and_arabic'),
    ]

    operations = [
        migrations.RenameModel('Governorate', 'Country'),
        migrations.RenameField('order', 'governorate', 'country'),
        migrations.RenameField('customerprofile', 'governorate', 'country'),
        migrations.AlterModelOptions(
            name='country',
            options={'ordering': ['ordering', 'name_ar'], 'verbose_name': 'دولة', 'verbose_name_plural': 'الدول'},
        ),
        migrations.AddField(
            model_name='country',
            name='code',
            field=models.CharField(blank=True, db_index=True, default='', help_text='ISO code, e.g. EG, SA, AE', max_length=2),
        ),
        migrations.AddField(
            model_name='country',
            name='free_shipping_over',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='فارغ = حد الشحن المجاني العام · 0 = مفيش شحن مجاني للدولة دي', max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='country',
            name='delivery_ar',
            field=models.CharField(blank=True, default='', max_length=80),
        ),
        migrations.AddField(
            model_name='country',
            name='delivery_en',
            field=models.CharField(blank=True, default='', max_length=80),
        ),
        migrations.AlterField(
            model_name='country',
            name='ordering',
            field=models.PositiveIntegerField(default=100),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
