"""الواجهة (Hero): زرار لتشغيل/إيقاف تأثير البني على صورة الواجهة."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0032_discord_url_work_thumbnail'),
    ]

    operations = [
        migrations.AddField(
            model_name='homesection', name='brown_tint',
            field=models.BooleanField(default=True),
        ),
    ]
