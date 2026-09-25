"""«حكايتنا»: قايمة أرقام واحدة — كل رقم يا بتكتبه بنفسك يا بيتحسب تلقائي.

- الأرقام اللي اتضافت قبل كده بقت بتظهر على طول (كانت مستخبية مع «أرقام تلقائية»).
- الأرقام التلقائية القديمة بقت صفوف في نفس القايمة؛ «عدد العملاء» بيتضاف مخفي.
"""

from django.db import migrations, models


def forwards(apps, schema_editor):
    AboutPage = apps.get_model('dashboard', 'AboutPage')
    AboutStat = apps.get_model('dashboard', 'AboutStat')
    page = AboutPage.objects.filter(pk=1).first()
    if page is None:
        return
    if page.stats_mode == 'hidden':
        page.stats_on_home = False
        page.stats_on_page = False
        page.save(update_fields=['stats_on_home', 'stats_on_page'])
        return
    if page.stats_mode != 'auto':
        return
    start = (AboutStat.objects.aggregate(m=models.Max('ordering'))['m'] or 0) + 1
    rows = [
        # (source, number written in the dashboard, suffix, star, shown)
        ('customers', page.customers_override, '+', False, page.customers_override is not None),
        ('products', page.products_override, '+', False, True),
        ('works', page.works_override, '+', False, True),
        ('rating', None, '', True, True),
    ]
    for i, (source, override, suffix, star, active) in enumerate(rows):
        if AboutStat.objects.filter(source=source).exists():
            continue
        AboutStat.objects.create(
            source=source, value='' if override is None else str(override),
            suffix=suffix, show_star=star, is_active=active, ordering=start + i,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0026_categories_sub_design'),
    ]

    operations = [
        migrations.AddField(
            model_name='aboutstat', name='source',
            field=models.CharField(
                choices=[
                    ('custom', 'رقم أنا بكتبه'),
                    ('customers', 'تلقائي — عدد العملاء المسجلين'),
                    ('products', 'تلقائي — عدد الديزاينات'),
                    ('works', 'تلقائي — عدد الأعمال'),
                    ('reviews', 'تلقائي — عدد التقييمات'),
                    ('rating', 'تلقائي — متوسط التقييم'),
                ],
                default='custom', max_length=12),
        ),
        migrations.AlterField(
            model_name='aboutstat', name='value',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AlterField(
            model_name='aboutstat', name='label_ar',
            field=models.CharField(blank=True, default='', max_length=60),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
