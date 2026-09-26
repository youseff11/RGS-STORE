"""شكل الرابط: اختيار «من غير صورة — كلام بس» (مفيش og:image خالص)."""

from django.db import migrations, models

CARD_CHOICES = [
    ('small', 'أيقونة صغيرة جنب الكلام'), ('large', 'صورة كبيرة تحت الكلام'), ('none', 'من غير صورة — كلام بس'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0030_link_card_style'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitesettings',
            name='share_card',
            field=models.CharField(choices=CARD_CHOICES, default='small', max_length=10),
        ),
        migrations.AlterField(
            model_name='linkpreview',
            name='card',
            field=models.CharField(
                blank=True, default='', max_length=10,
                choices=[('', 'زي الإعداد الافتراضي')] + CARD_CHOICES,
            ),
        ),
    ]
