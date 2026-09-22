"""«حكايتنا» — تحكم كامل من الداشبورد: الكلمة اللي على الصورة، الأرقام، وصفحة «من نحن»."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0018_work_media_links'),
    ]

    operations = [
        migrations.CreateModel(
            name='AboutPage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag_ar', models.CharField(blank=True, default='', max_length=80)),
                ('tag_en', models.CharField(blank=True, default='', max_length=80)),
                ('show_tag', models.BooleanField(default=True)),
                ('stats_mode', models.CharField(
                    choices=[
                        ('auto', 'أرقام تلقائية (عدد العملاء والديزاينات والأعمال والتقييم)'),
                        ('custom', 'أرقام أنا اللي بكتبها'),
                        ('hidden', 'من غير أرقام'),
                    ], default='auto', max_length=10)),
                ('stats_on_home', models.BooleanField(default=True)),
                ('stats_on_page', models.BooleanField(default=True)),
                ('page_title_ar', models.CharField(blank=True, default='', max_length=160)),
                ('page_title_en', models.CharField(blank=True, default='', max_length=160)),
                ('page_subtitle_ar', models.CharField(blank=True, default='', max_length=300)),
                ('page_subtitle_en', models.CharField(blank=True, default='', max_length=300)),
                ('page_image', models.ImageField(blank=True, null=True, upload_to='site/')),
                ('button1_text_ar', models.CharField(blank=True, default='تسوّق الآن', max_length=60)),
                ('button1_text_en', models.CharField(blank=True, default='Shop now', max_length=60)),
                ('button1_link', models.CharField(blank=True, default='/shop/', max_length=300)),
                ('button2_text_ar', models.CharField(blank=True, default='أعمالنا', max_length=60)),
                ('button2_text_en', models.CharField(blank=True, default='Our work', max_length=60)),
                ('button2_link', models.CharField(blank=True, default='/works/', max_length=300)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='AboutStat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=20)),
                ('suffix', models.CharField(blank=True, default='+', help_text='مثلاً + أو % أو K', max_length=6)),
                ('show_star', models.BooleanField(default=False)),
                ('label_ar', models.CharField(max_length=60)),
                ('label_en', models.CharField(blank=True, default='', max_length=60)),
                ('is_active', models.BooleanField(default=True)),
                ('ordering', models.PositiveIntegerField(default=0)),
            ],
            options={'ordering': ['ordering', 'id']},
        ),
    ]
