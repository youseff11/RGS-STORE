"""«الدخول بجوجل» — مفاتيح OAuth في الإعدادات + ربط حساب العميل بحساب جوجل."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0007_support_nav_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='google_login_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='google_client_id',
            field=models.CharField(
                blank=True, default='', max_length=255,
                help_text='من Google Cloud Console — بينتهي بـ .apps.googleusercontent.com',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='google_client_secret',
            field=models.CharField(
                blank=True, default='', max_length=255,
                help_text='الـ Client secret من نفس الشاشة — بيتحفظ عندنا ومش بيظهر تاني',
            ),
        ),
        migrations.AddField(
            model_name='customerprofile',
            name='google_id',
            field=models.CharField(blank=True, db_index=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='customerprofile',
            name='google_picture',
            field=models.URLField(blank=True, default='', max_length=500),
        ),
    ]
