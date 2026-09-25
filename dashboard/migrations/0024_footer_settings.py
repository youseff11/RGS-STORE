"""«الفوتر» — نصوص الفوتر وإظهار/إخفاء أجزاءه من الداشبورد."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0023_social_icon_filefield'),
    ]

    operations = [
        migrations.AddField(model_name='sitesettings', name='footer_text_ar', field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='sitesettings', name='footer_text_en', field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='sitesettings', name='footer_show_logo', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='sitesettings', name='footer_show_text', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='sitesettings', name='footer_show_socials', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='sitesettings', name='footer_show_shop', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='sitesettings', name='footer_shop_title_ar', field=models.CharField(max_length=60, blank=True, default='')),
        migrations.AddField(model_name='sitesettings', name='footer_shop_title_en', field=models.CharField(max_length=60, blank=True, default='')),
        migrations.AddField(model_name='sitesettings', name='footer_show_help', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='sitesettings', name='footer_help_title_ar', field=models.CharField(max_length=60, blank=True, default='')),
        migrations.AddField(model_name='sitesettings', name='footer_help_title_en', field=models.CharField(max_length=60, blank=True, default='')),
        migrations.AddField(model_name='sitesettings', name='footer_show_policies', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='sitesettings', name='footer_show_contact', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='sitesettings', name='footer_contact_title_ar', field=models.CharField(max_length=60, blank=True, default='')),
        migrations.AddField(model_name='sitesettings', name='footer_contact_title_en', field=models.CharField(max_length=60, blank=True, default='')),
        migrations.AddField(model_name='sitesettings', name='footer_show_phone', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='sitesettings', name='footer_show_email', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='sitesettings', name='footer_show_address', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='sitesettings', name='footer_show_payment', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='sitesettings', name='footer_payment_text_ar', field=models.CharField(max_length=120, blank=True, default='')),
        migrations.AddField(model_name='sitesettings', name='footer_payment_text_en', field=models.CharField(max_length=120, blank=True, default='')),
        migrations.AddField(model_name='sitesettings', name='footer_copyright_ar', field=models.CharField(max_length=200, blank=True, default='')),
        migrations.AddField(model_name='sitesettings', name='footer_copyright_en', field=models.CharField(max_length=200, blank=True, default='')),
        migrations.AddField(model_name='sitesettings', name='footer_show_back_to_top', field=models.BooleanField(default=True)),
    ]
