"""صورة لحساب العميل — بيرفعها من «بياناتي» وبتظهر في تقييماته وفي الموقع."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0016_link_previews'),
    ]

    operations = [
        migrations.AddField(
            model_name='customerprofile',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/'),
        ),
    ]
