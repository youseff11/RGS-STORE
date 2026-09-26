"""شكل الرابط لما يتبعت: أيقونة صغيرة جنب الكلام (زي ديسكورد) أو صورة كبيرة + لون الخط الجانبي."""

from django.db import migrations, models

CARD_CHOICES = [('small', 'أيقونة صغيرة جنب الكلام'), ('large', 'صورة كبيرة تحت الكلام')]


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0029_link_preview_optional_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='share_card',
            field=models.CharField(choices=CARD_CHOICES, default='small', max_length=10),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='share_color',
            field=models.CharField(default='#B04B00', max_length=7),
        ),
        migrations.AddField(
            model_name='linkpreview',
            name='card',
            field=models.CharField(
                blank=True, default='', max_length=10,
                choices=[('', 'زي الإعداد الافتراضي')] + CARD_CHOICES,
            ),
        ),
    ]
