"""«صور الروابط»: الصورة بقت اختيارية — ممكن رابط بعنوان/وصف بس من غير صورة."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0028_product_fees'),
    ]

    operations = [
        migrations.AlterField(
            model_name='linkpreview',
            name='image',
            field=models.ImageField(
                blank=True, upload_to='share/',
                help_text='اختياري — لو فاضية الرابط بياخد صورة الصفحة نفسها أو الصورة الافتراضية',
            ),
        ),
    ]
