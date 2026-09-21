"""كلام الـ Hero بقى بتاع خدمات جرافيك بدل محل الملابس.

بيغيّر بس الخانات اللي لسه على الكلام الافتراضي القديم — أي حاجة مالك كتبها بنفسه من
«الصفحة الرئيسية» في الداشبورد بتفضل زي ما هي.
"""

from django.db import migrations

OLD = {
    'eyebrow_ar': 'موسم جديد', 'eyebrow_en': 'NEW SEASON',
    'title_ar': 'البس\nثقتك', 'title_en': 'WEAR YOUR\nCONFIDENCE',
    'subtitle_ar': 'خامات ممتازة. ستايلات مودرن. معمولة عشانك.',
    'subtitle_en': 'Premium quality. Modern styles. Made for you.',
    'button_text_ar': 'تسوّق الآن', 'button_text_en': 'SHOP NOW',
}
NEW = {
    'eyebrow_ar': 'استوديو جرافيك', 'eyebrow_en': 'CREATIVE STUDIO',
    'title_ar': 'صمّم\nهويتك', 'title_en': 'DESIGN YOUR\nIDENTITY',
    'subtitle_ar': 'لوجوهات وسوشيال ميديا وتصميمات طباعة — بألوانك وعلى ذوقك.',
    'subtitle_en': 'Logos, social media & print — designed in your colors.',
    'button_text_ar': 'اكتشف التصميمات', 'button_text_en': 'EXPLORE DESIGNS',
}


def _norm(value):
    return (value or '').replace('\\n', '\n').replace('\r\n', '\n').strip()


def swap(apps, old, new):
    HomeSection = apps.get_model('dashboard', 'HomeSection')
    for section in HomeSection.objects.filter(key='hero'):
        changed = []
        for field, old_value in old.items():
            if _norm(getattr(section, field)) == _norm(old_value):
                setattr(section, field, new[field])
                changed.append(field)
        if changed:
            section.save(update_fields=changed)


def forwards(apps, schema_editor):
    swap(apps, OLD, NEW)


def backwards(apps, schema_editor):
    swap(apps, NEW, OLD)


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0010_discord_login'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
