"""Compress the pictures that were uploaded before auto-compression existed.

    python manage.py compress_images            # do it
    python manage.py compress_images --dry-run  # just show what would shrink
"""

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db.models import FileField, ImageField

from dashboard.image_optim import (
    JPEG_FIELDS, SKIP_EXTS, SKIP_FIELDS, _max_side, _new_name, compress_bytes,
)


class Command(BaseCommand):
    help = 'Resize + re-encode existing uploaded images (WebP) to make the site load faster.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, dry_run=False, **options):
        from django.apps import apps

        before_total = after_total = done = 0
        for model in apps.get_app_config('dashboard').get_models():
            key = model._meta.model_name
            fields = [
                f for f in model._meta.fields
                if isinstance(f, ImageField) or (key == 'ticketattachment' and isinstance(f, FileField))
            ]
            fields = [f for f in fields if (key, f.name) not in SKIP_FIELDS]
            if not fields:
                continue
            for obj in model.objects.all().iterator():
                if key == 'ticketattachment' and obj.kind != 'image':
                    continue
                for field in fields:
                    file = getattr(obj, field.attname)
                    if not file or not file.name:
                        continue
                    ext = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''
                    if ext in SKIP_EXTS:
                        continue
                    try:
                        with file.storage.open(file.name, 'rb') as fh:
                            raw = fh.read()
                    except (FileNotFoundError, OSError):
                        continue
                    fmt = 'JPEG' if (key, field.name) in JPEG_FIELDS else 'WEBP'
                    max_side = min(_max_side(field.upload_to), 1200) if fmt == 'JPEG' else _max_side(field.upload_to)
                    result = compress_bytes(raw, max_side=max_side, fmt=fmt)
                    if result is None:
                        continue
                    data, new_ext = result
                    if len(data) >= len(raw) * 0.9:
                        continue  # not worth it
                    before_total += len(raw)
                    after_total += len(data)
                    done += 1
                    self.stdout.write(f'{file.name}: {len(raw) // 1024} KB → {len(data) // 1024} KB')
                    if dry_run:
                        continue
                    old_name = file.name
                    storage = file.storage
                    file.save(_new_name(old_name, new_ext), ContentFile(data), save=False)
                    updates = [field.name]
                    if key == 'ticketattachment':
                        obj.size = len(data)
                        updates.append('size')
                    # update() skips save() side effects (slugs, signals…)
                    model.objects.filter(pk=obj.pk).update(**{f: getattr(obj, f) for f in updates})
                    if storage.exists(old_name) and old_name != file.name:
                        storage.delete(old_name)

        label = 'would shrink' if dry_run else 'compressed'
        self.stdout.write(self.style.SUCCESS(
            f'{label} {done} images: {before_total // 1024} KB → {after_total // 1024} KB'
        ))
