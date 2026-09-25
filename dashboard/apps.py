from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'
    verbose_name = 'RGS TOWER'

    def ready(self):
        # every picture uploaded anywhere in the app gets resized + compressed
        from django.db.models.signals import pre_save

        from .image_optim import compress_uploads

        for model in self.get_models():
            pre_save.connect(compress_uploads, sender=model, dispatch_uid=f'compress-{model._meta.label}')
