"""المقاسات بقت «خدمات» — المشروع اتحول من محل ملابس لخدمات جرافيك.

- الموديل `Size` اتغيّر اسمه لـ `Service` (اسم عربي مطلوب + إنجليزي اختياري + سعر إضافي + تشغيل/إيقاف).
- `ProductVariant.size` → `service`، و`OrderItem.size_name` → `service_name`.
- الخدمات ملهاش مخزون: `ProductVariant.quantity` و`SiteSettings.low_stock_threshold`
  و`Order.stock_restored` اتشالوا.
- المقاسات الافتراضية (S / M / L / XL / 2XL / 3XL) بتتمسح علشان مالك يكتب الخدمات بنفسه.
  أي منتج كان عليها بيفضل متاح بألوانه (variant لكل لون من غير خدمة)، والطلبات القديمة
  بتحتفظ باسم المقاس مكتوب زي ما هو.
- أي مقاس تاني كان مالك زوّده بإيده بيتحول لخدمة بنفس الاسم.
"""

from django.db import migrations, models

DEFAULT_SIZES = {'XS', 'S', 'M', 'L', 'XL', 'XXL', '2XL', 'XXXL', '3XL'}


def drop_clothing_sizes(apps, schema_editor):
    Size = apps.get_model('dashboard', 'Size')
    Variant = apps.get_model('dashboard', 'ProductVariant')
    defaults = list(Size.objects.filter(name__in=DEFAULT_SIZES))
    if not defaults:
        return
    for variant in Variant.objects.filter(size__in=defaults):
        # keep the design orderable in this colour, just without a size
        exists = Variant.objects.filter(
            product_id=variant.product_id, color_id=variant.color_id, size__isnull=True,
        ).exists()
        if not exists:
            Variant.objects.create(
                product_id=variant.product_id, color_id=variant.color_id, size=None, quantity=0,
            )
    Size.objects.filter(pk__in=[s.pk for s in defaults]).delete()  # their variants go with them


def fill_arabic_names(apps, schema_editor):
    Service = apps.get_model('dashboard', 'Service')
    for service in Service.objects.filter(name_ar=''):
        service.name_ar = service.name_en
        service.save(update_fields=['name_ar'])


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0008_google_login'),
    ]

    operations = [
        migrations.RemoveConstraint(model_name='productvariant', name='uniq_product_color_size'),
        migrations.RunPython(drop_clothing_sizes, migrations.RunPython.noop),

        # Size → Service
        migrations.RenameModel('Size', 'Service'),
        migrations.RenameField('service', 'name', 'name_en'),
        migrations.AlterField(
            model_name='service',
            name='name_en',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
        migrations.AlterField(
            model_name='service',
            name='name_ar',
            field=models.CharField(max_length=120),
        ),
        migrations.RunPython(fill_arabic_names, migrations.RunPython.noop),
        migrations.AddField(
            model_name='service',
            name='price',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=10,
                help_text='بيتزوّد على سعر الديزاين — 0 = من غير زيادة',
            ),
        ),
        migrations.AddField(
            model_name='service',
            name='is_active',
            field=models.BooleanField(default=True),
        ),

        # variants: colour × service, no stock
        migrations.RenameField('productvariant', 'size', 'service'),
        migrations.RemoveField(model_name='productvariant', name='quantity'),
        migrations.AlterModelOptions(
            name='productvariant',
            options={'ordering': ['color__ordering', 'service__ordering', 'id']},
        ),
        migrations.AddConstraint(
            model_name='productvariant',
            constraint=models.UniqueConstraint(
                fields=('product', 'color', 'service'), name='uniq_product_color_service',
            ),
        ),

        # order lines keep the service name as text
        migrations.RenameField('orderitem', 'size_name', 'service_name'),
        migrations.AlterField(
            model_name='orderitem',
            name='service_name',
            field=models.CharField(blank=True, default='', max_length=160),
        ),

        # stock bookkeeping is gone
        migrations.RemoveField(model_name='sitesettings', name='low_stock_threshold'),
        migrations.RemoveField(model_name='order', name='stock_restored'),
    ]
