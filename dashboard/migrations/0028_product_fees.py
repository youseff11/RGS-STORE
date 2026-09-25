"""«الضرائب والرسوم التحويلي والبنكي» على المنتج — بتتضاف على الطلب لو الدفع بـ PayPal بس."""

from decimal import Decimal

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0027_about_stat_sources'),
    ]

    operations = [
        migrations.AddField(
            model_name='product', name='fees_type',
            field=models.CharField(
                choices=[('percent', 'نسبة % من سعر المنتج'), ('fixed', 'مبلغ ثابت على كل قطعة')],
                default='percent', max_length=8),
        ),
        migrations.AddField(
            model_name='product', name='fees_value',
            field=models.DecimalField(
                decimal_places=2, default=Decimal('0.00'), max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0.00'))]),
        ),
        migrations.AddField(
            model_name='order', name='fees_total',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
    ]
