"""أنواع التذاكر بقت خاصة بخدمات الجرافيك بدل محل الملابس.

التذاكر القديمة بتتنقل لأقرب نوع جديد علشان ما يفضلش فيه تذكرة بنوع مش موجود.
"""

from django.db import migrations, models

OLD_TO_NEW = {
    'order': 'inquiry',
    'product': 'buy_product',
    'shipping': 'paid_delivery',
    'payment': 'inquiry',
    'return': 'inquiry',
}


def forwards(apps, schema_editor):
    Ticket = apps.get_model('dashboard', 'Ticket')
    for old, new in OLD_TO_NEW.items():
        Ticket.objects.filter(topic=old).update(topic=new)


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0011_graphic_hero_copy'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='topic',
            field=models.CharField(
                choices=[
                    ('buy_product', 'شراء منتج'),
                    ('service', 'طلب خدمة'),
                    ('partnership', 'شراكة | إعلانات'),
                    ('paid_delivery', 'استلام منتج مدفوع'),
                    ('inquiry', 'استفسارات'),
                    ('other', 'أخرى'),
                ],
                default='other',
                max_length=20,
            ),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
