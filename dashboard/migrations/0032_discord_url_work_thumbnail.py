"""رابط ديسكورد في «السوشيال ميديا» + صورة مصغرة للعمل (تقبل GIF)."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0031_link_card_no_image'),
    ]

    operations = [
        migrations.AddField(model_name='sitesettings', name='discord_url',
                            field=models.URLField(blank=True, default='')),
        migrations.AddField(
            model_name='work', name='thumbnail',
            field=models.ImageField(
                blank=True, null=True, upload_to='works/thumbs/',
                help_text='الصورة اللي بتظهر في كارت العمل — تقدر ترفع GIF متحرك. لو فاضية بيظهر البانر',
            ),
        ),
    ]
