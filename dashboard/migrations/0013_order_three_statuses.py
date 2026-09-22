"""حالات الطلب بقت 3 بس للعميل: تم استلام طلبك ← جاري العمل ← تم التسليم (+ ملغي للأدمن).

الطلبات اللي كانت «تم الشحن» بتتحوّل «جاري العمل».
"""

from django.db import migrations, models


def forwards(apps, schema_editor):
    Order = apps.get_model('dashboard', 'Order')
    Order.objects.filter(status='shipped').update(status='confirmed')


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0012_graphic_ticket_topics'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'تم استلام طلبك / Order received'),
                    ('confirmed', 'جاري العمل / In progress'),
                    ('delivered', 'تم التسليم / Delivered'),
                    ('cancelled', 'ملغي / Cancelled'),
                ],
                default='pending',
                max_length=12,
            ),
        ),
    ]
