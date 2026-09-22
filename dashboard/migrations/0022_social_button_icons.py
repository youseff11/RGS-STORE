"""أيقونة زرار الدخول بجوجل / ديسكورد — بترفعها من الداشبورد."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0021_about_count_overrides'),
    ]

    operations = [
        migrations.AddField(model_name='sitesettings', name='google_button_icon',
                            field=models.ImageField(blank=True, null=True, upload_to='site/')),
        migrations.AddField(model_name='sitesettings', name='discord_button_icon',
                            field=models.ImageField(blank=True, null=True, upload_to='site/')),
    ]
