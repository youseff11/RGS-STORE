"""فيديوهات «أعمالنا» من لينك: مواقع أكتر ولينكات أطول (فيسبوك / درايف بيبقوا طوال)."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0017_customer_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workmedia',
            name='embed_url',
            field=models.URLField(blank=True, default='', max_length=1000),
        ),
        migrations.AlterField(
            model_name='workmedia',
            name='kind',
            field=models.CharField(
                choices=[('image', 'صورة'), ('video', 'فيديو مرفوع'), ('embed', 'فيديو من لينك')],
                default='image', max_length=10,
            ),
        ),
    ]
