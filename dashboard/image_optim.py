"""Shrink every uploaded picture before it hits the disk.

Any ImageField in the dashboard app (plus picture attachments on support tickets)
is resized to a sensible maximum and re-encoded as WebP (JPEG for link-preview
images, since some apps still don't show WebP previews). A 4 MB phone photo
usually ends up around 150–400 KB with no visible difference.

Hooked up in DashboardConfig.ready() through a pre_save signal, so it covers the
dashboard forms, the Django admin and the customer pages alike.
"""

import io
import logging
import os

from django.core.files.base import ContentFile
from django.db.models import FileField, ImageField

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageOps
except ImportError:  # Pillow missing → uploads keep working, just uncompressed
    Image = None

WEBP_QUALITY = 80
JPEG_QUALITY = 82
DEFAULT_MAX = 1920

# longest side (px) per upload folder — anything bigger gets scaled down
MAX_BY_FOLDER = {
    'home/': 2400,          # hero / homepage sections
    'banners/': 2400,
    'site/': 1600,          # logo, about page picture…
    'products/': 1600,
    'categories/': 1000,
    'works/covers/': 2000,
    'works/media/': 2000,
    'works/posters/': 1600,
    'avatars/': 400,
    'share/': 1200,
    'tickets/': 1600,
}

# fields left exactly as uploaded
SKIP_FIELDS = {
    ('sitesettings', 'favicon'),              # browsers want a small PNG/ICO
    ('sitesettings', 'google_button_icon'),   # tiny icons, may be SVG
    ('sitesettings', 'discord_button_icon'),
}

# link previews (WhatsApp / Facebook) → JPEG, 1200px wide
JPEG_FIELDS = {
    ('sitesettings', 'share_image'),
    ('linkpreview', 'image'),
}

SKIP_EXTS = {'svg', 'gif', 'ico', 'heic', 'heif'}  # vector / animated / unsupported


def _max_side(upload_to):
    folder = upload_to if isinstance(upload_to, str) else ''
    for prefix, size in MAX_BY_FOLDER.items():
        if folder.startswith(prefix):
            return size
    return DEFAULT_MAX


def compress_bytes(raw, max_side=DEFAULT_MAX, fmt='WEBP'):
    """Return (data, ext) for the compressed picture, or None to keep the original."""
    if Image is None:
        return None
    try:
        img = Image.open(io.BytesIO(raw))
        if getattr(img, 'is_animated', False) and img.n_frames > 1:
            return None
        img = ImageOps.exif_transpose(img)
    except Exception:  # not an image Pillow can read
        return None

    has_alpha = img.mode in ('RGBA', 'LA', 'PA') or (img.mode == 'P' and 'transparency' in img.info)
    if fmt == 'JPEG':
        if has_alpha:
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img.convert('RGBA'), mask=img.convert('RGBA').split()[-1])
            img = bg
        else:
            img = img.convert('RGB')
    else:
        img = img.convert('RGBA' if has_alpha else 'RGB')

    resized = False
    if max(img.size) > max_side:
        img.thumbnail((max_side, max_side), Image.LANCZOS)
        resized = True

    out = io.BytesIO()
    if fmt == 'JPEG':
        img.save(out, 'JPEG', quality=JPEG_QUALITY, optimize=True, progressive=True)
        ext = 'jpg'
    else:
        img.save(out, 'WEBP', quality=WEBP_QUALITY, method=6)
        ext = 'webp'
    data = out.getvalue()

    # already small & light enough → keep what the user uploaded
    if not resized and len(data) >= len(raw):
        return None
    return data, ext


def _new_name(old_name, ext):
    base = os.path.splitext(os.path.basename(old_name or 'image'))[0] or 'image'
    return f'{base[:80]}.{ext}'


def compress_field_file(instance, field):
    """Compress the file sitting on `instance.<field>` if it was just uploaded."""
    model_key = instance._meta.model_name
    if (model_key, field.name) in SKIP_FIELDS:
        return False
    file = getattr(instance, field.attname)
    if not file or getattr(file, '_committed', True):
        return False  # empty, or already saved on disk (not a new upload)

    ext = file.name.rsplit('.', 1)[-1].lower() if '.' in (file.name or '') else ''
    if ext in SKIP_EXTS:
        return False

    try:
        file.seek(0)
        raw = file.read()
        file.seek(0)
    except Exception:
        return False

    fmt = 'JPEG' if (model_key, field.name) in JPEG_FIELDS else 'WEBP'
    max_side = _max_side(field.upload_to)
    if fmt == 'JPEG':
        max_side = min(max_side, 1200)
    result = compress_bytes(raw, max_side=max_side, fmt=fmt)
    if result is None:
        return False

    data, new_ext = result
    setattr(instance, field.attname, ContentFile(data, name=_new_name(file.name, new_ext)))
    logger.info('compressed %s.%s: %d KB → %d KB', model_key, field.name, len(raw) // 1024, len(data) // 1024)
    return True


def compress_uploads(sender, instance, **kwargs):
    """pre_save hook: compress every freshly uploaded picture on the instance."""
    if kwargs.get('raw'):  # loaddata
        return
    is_attachment = sender._meta.model_name == 'ticketattachment'
    for field in sender._meta.fields:
        if isinstance(field, ImageField):
            compress_field_file(instance, field)
        elif is_attachment and isinstance(field, FileField) and getattr(instance, 'kind', '') == 'image':
            if compress_field_file(instance, field):
                instance.size = getattr(instance, field.attname).size
