"""Put «الدعم» in the storefront menu.

The tickets page only helps if customers can find it, so the link is added to
the existing menu once (staff never see it — the header hides it for them).
The owner can rename it, move it or switch it off from «القائمة (الناف بار)».
"""

from django.db import migrations


def forwards(apps, schema_editor):
    NavLink = apps.get_model('dashboard', 'NavLink')
    if not NavLink.objects.exists() or NavLink.objects.filter(link_type='support').exists():
        return
    last = NavLink.objects.order_by('-ordering').values_list('ordering', flat=True).first() or 0
    NavLink.objects.create(link_type='support', ordering=last + 1)


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0006_navlink_support'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
