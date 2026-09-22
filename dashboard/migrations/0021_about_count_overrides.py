"""أرقام «حكايتنا» التلقائية: تقدر تكتب عدد العملاء / الديزاينات / الأعمال بنفسك أو تسيبه حقيقي."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0020_hero_controls'),
    ]

    operations = [
        migrations.AddField(model_name='aboutpage', name='customers_override',
                            field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField(model_name='aboutpage', name='products_override',
                            field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField(model_name='aboutpage', name='works_override',
                            field=models.PositiveIntegerField(blank=True, null=True)),
    ]
