"""اسم العميل في التقييمات بقى ثنائي كامل («أحمد محمد» بدل «أحمد م.»).

بيغيّر بس الأسماء اللي لسه بالشكل المختصر القديم — أي اسم انت عدّلته بإيدك من الداشبورد بيفضل زي ما هو.
"""

from django.db import migrations


def _old_name(first, last):
    first, last = (first or '').strip(), (last or '').strip()
    if first:
        return f'{first} {last[:1]}.' if last else first
    return None


def _new_name(first, last, fallback):
    words = f'{first or ""} {last or ""}'.split()
    if len(words) < 2:
        backup = (fallback or '').split('@')[0].split()
        if len(backup) > len(words):
            words = backup
    return ' '.join(words[:2])


def forwards(apps, schema_editor):
    Review = apps.get_model('dashboard', 'Review')
    for review in Review.objects.select_related('user', 'order'):
        user = review.user
        old = _old_name(user.first_name, user.last_name)
        if old is None or review.name != old[:120]:
            continue
        fallback = review.order.full_name if review.order_id else ''
        new = _new_name(user.first_name, user.last_name, fallback)[:120]
        if new and new != review.name:
            Review.objects.filter(pk=review.pk).update(name=new)


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0014_reviews_auto_publish'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
