"""«صور الروابط» — صورة وعنوان خاصين لأي رابط من الموقع لما يتبعت."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0015_review_two_part_names'),
    ]

    operations = [
        migrations.CreateModel(
            name='LinkPreview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(max_length=300, unique=True)),
                ('match_children', models.BooleanField(
                    default=False, help_text='مثلاً /policies/ → كل صفحات السياسات تاخد نفس الصورة')),
                ('image', models.ImageField(upload_to='share/')),
                ('title_ar', models.CharField(blank=True, default='', max_length=160)),
                ('title_en', models.CharField(blank=True, default='', max_length=160)),
                ('description_ar', models.CharField(blank=True, default='', max_length=300)),
                ('description_en', models.CharField(blank=True, default='', max_length=300)),
                ('is_active', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['path']},
        ),
    ]
