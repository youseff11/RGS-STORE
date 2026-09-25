"""الواجهة (Hero): زرار لإظهار/إخفاء الكلام المكتوب بخط اليد (Bold Ideas Better Designs)."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0024_footer_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='homesection', name='show_script',
            field=models.BooleanField(default=True),
        ),
    ]
