from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('fms', '0062_alter_externalflightevaluation_course_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='externalflightevaluation',
            name='fuel_rate_applied',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('3.11'),
                max_digits=6,
                verbose_name='Tarifa de combustible aplicada ($/litro)',
            ),
        ),
        migrations.AddField(
            model_name='flightreport',
            name='fuel_rate_applied',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('3.11'),
                max_digits=6,
                verbose_name='Tarifa de combustible aplicada ($/litro)',
            ),
        ),
    ]
