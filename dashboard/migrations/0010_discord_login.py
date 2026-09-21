"""«الدخول بديسكورد» — مفاتيح OAuth في الإعدادات + ربط حساب العميل بحساب ديسكورد."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0009_services'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='discord_login_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='discord_client_id',
            field=models.CharField(
                blank=True, default='', max_length=64,
                help_text='من Discord Developer Portal ← OAuth2 — رقم طويل',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='discord_client_secret',
            field=models.CharField(
                blank=True, default='', max_length=255,
                help_text='الـ Client secret من نفس الشاشة — بيتحفظ عندنا ومش بيظهر تاني',
            ),
        ),
        migrations.AddField(
            model_name='customerprofile',
            name='discord_id',
            field=models.CharField(blank=True, db_index=True, default='', max_length=32),
        ),
        migrations.AddField(
            model_name='customerprofile',
            name='discord_avatar',
            field=models.URLField(blank=True, default='', max_length=500),
        ),
    ]
