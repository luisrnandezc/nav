# Help text: weights are any nonnegative pair summing to 1 (not only 1/0 or 0.8/0.2).

import django.core.validators
from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academic', '0038_alter_subjectedition_practical_weight_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subjectedition',
            name='theory_weight',
            field=models.DecimalField(
                decimal_places=3,
                default=Decimal('1'),
                help_text='Fracción del examen final atribuida a teoría. Debe sumar 1.0 con el peso de práctica (ej. 1 y 0, o 0.7 y 0.3).',
                max_digits=4,
                validators=[
                    django.core.validators.MinValueValidator(Decimal('0')),
                    django.core.validators.MaxValueValidator(Decimal('1')),
                ],
                verbose_name='Peso teoría',
            ),
        ),
        migrations.AlterField(
            model_name='subjectedition',
            name='practical_weight',
            field=models.DecimalField(
                decimal_places=3,
                default=Decimal('0'),
                help_text='Fracción del examen final atribuida a práctica. Debe sumar 1.0 con el peso de teoría.',
                max_digits=4,
                validators=[
                    django.core.validators.MinValueValidator(Decimal('0')),
                    django.core.validators.MaxValueValidator(Decimal('1')),
                ],
                verbose_name='Peso práctica',
            ),
        ),
    ]
