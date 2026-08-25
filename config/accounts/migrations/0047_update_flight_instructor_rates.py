from decimal import Decimal

from django.db import migrations, models


def update_current_instructor_rates(apps, schema_editor):
    """Set current flight rates from the stored chief-instructor designation."""

    InstructorProfile = apps.get_model('accounts', 'InstructorProfile')
    instructor_count = InstructorProfile.objects.count()
    chief_count = InstructorProfile.objects.filter(is_chief_instructor=True).count()
    if instructor_count and chief_count != 1:
        raise RuntimeError(
            'Select exactly one chief instructor before updating flight rates.'
        )

    InstructorProfile.objects.filter(is_chief_instructor=False).update(
        flight_instructor_hourly_rate=Decimal('25.0'),
    )
    InstructorProfile.objects.filter(is_chief_instructor=True).update(
        flight_instructor_hourly_rate=Decimal('30.0'),
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0046_remove_instructorprofile_is_chief_flight_instructor_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instructorprofile',
            name='flight_instructor_hourly_rate',
            field=models.DecimalField(
                decimal_places=1,
                default=25.0,
                max_digits=3,
                verbose_name='Tasa instrucción vuelo ($/h)',
            ),
        ),
        migrations.RunPython(
            update_current_instructor_rates,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
