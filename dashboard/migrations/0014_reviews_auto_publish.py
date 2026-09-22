"""تقييمات العملاء بتتنشر أوتوماتيك أول ما العميل يكتبها.

- النشر التلقائي بقى شغّال (تقدر تقفله من «إعدادات المتجر»).
- التقييمات اللي كانت مستنية موافقة ومحدش لمسها بتتنشر — أي تقييم انت خفيته بإيدك بيفضل مخفي.
"""

from datetime import timedelta

from django.db import migrations, models


def forwards(apps, schema_editor):
    SiteSettings = apps.get_model('dashboard', 'SiteSettings')
    Review = apps.get_model('dashboard', 'Review')
    SiteSettings.objects.update(reviews_auto_publish=True)
    untouched = [
        r.pk for r in Review.objects.filter(is_approved=False)
        if r.updated_at - r.created_at < timedelta(seconds=5)
    ]
    Review.objects.filter(pk__in=untouched).update(is_approved=True)


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0013_order_three_statuses'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitesettings',
            name='reviews_auto_publish',
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
