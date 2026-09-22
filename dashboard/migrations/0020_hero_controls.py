"""الواجهة (Hero): صورة للموبايل، مكان الصورة، والكلام المكتوب بخط اليد — كله من الداشبورد."""

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0019_about_story'),
    ]

    operations = [
        migrations.AddField(
            model_name='homesection', name='image_mobile',
            field=models.ImageField(blank=True, null=True, upload_to='home/'),
        ),
        migrations.AddField(
            model_name='homesection', name='image_focus',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True, validators=[django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AddField(
            model_name='homesection', name='image_focus_mobile',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True, validators=[django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AddField(
            model_name='homesection', name='script_text',
            field=models.CharField(blank=True, default='', max_length=160),
        ),
    ]
