from decimal import Decimal

from django.db import migrations


FLIGHT_EVALUATION_MODELS = (
    'FlightEvaluation0_100',
    'FlightEvaluation100_120',
    'FlightEvaluation120_170',
)


def update_historical_instructor_rates(apps, schema_editor):
    """Apply standard and chief rates to every internal flight snapshot."""

    InstructorProfile = apps.get_model('accounts', 'InstructorProfile')
    chief_ids = list(
        InstructorProfile.objects.filter(is_chief_instructor=True).values_list(
            'user__national_id',
            flat=True,
        )
    )

    for model_name in FLIGHT_EVALUATION_MODELS:
        evaluation_model = apps.get_model('fms', model_name)
        evaluation_model.objects.update(
            instructor_rate_applied=Decimal('25.00'),
        )
        if chief_ids:
            evaluation_model.objects.filter(instructor_id__in=chief_ids).update(
                instructor_rate_applied=Decimal('30.00'),
            )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0047_update_flight_instructor_rates'),
        ('fms', '0064_production_rate_snapshots'),
    ]

    operations = [
        migrations.RunPython(
            update_historical_instructor_rates,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
