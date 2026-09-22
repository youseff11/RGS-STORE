"""أيقونة زرار جوجل / ديسكورد بقت تقبل SVG كمان (مش صور بس)."""

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0022_social_button_icons'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitesettings', name='google_button_icon',
            field=models.FileField(
                blank=True, null=True, upload_to='site/',
                validators=[django.core.validators.FileExtensionValidator(
                    ['png', 'svg', 'webp', 'jpg', 'jpeg'])]),
        ),
        migrations.AlterField(
            model_name='sitesettings', name='discord_button_icon',
            field=models.FileField(
                blank=True, null=True, upload_to='site/',
                validators=[django.core.validators.FileExtensionValidator(
                    ['png', 'svg', 'webp', 'jpg', 'jpeg'])]),
        ),
    ]
