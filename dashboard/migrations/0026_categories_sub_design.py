"""«اختار القسم اللي يناسب ستايلك» ← «تصميمك» (بيغيّر النص القديم بس لو محدش عدّله)."""

from django.db import migrations

OLD = ('اختار القسم اللي يناسب ستايلك', 'Pick the section that fits your style')
NEW = ('اختار القسم اللي يناسب تصميمك', 'Pick the section that fits your design')


def forwards(apps, schema_editor):
    HomeSection = apps.get_model('dashboard', 'HomeSection')
    HomeSection.objects.filter(subtitle_ar=OLD[0]).update(subtitle_ar=NEW[0])
    HomeSection.objects.filter(subtitle_en=OLD[1]).update(subtitle_en=NEW[1])


def backwards(apps, schema_editor):
    HomeSection = apps.get_model('dashboard', 'HomeSection')
    HomeSection.objects.filter(subtitle_ar=NEW[0]).update(subtitle_ar=OLD[0])
    HomeSection.objects.filter(subtitle_en=NEW[1]).update(subtitle_en=OLD[1])


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0025_hero_show_script'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
