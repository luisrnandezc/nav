from decimal import Decimal

from django.db import migrations, models


FLIGHT_MODELS = (
    'FlightEvaluation0_100',
    'FlightEvaluation100_120',
    'FlightEvaluation120_170',
)


def backfill_rate_snapshots(apps, schema_editor):
    InstructorProfile = apps.get_model('accounts', 'InstructorProfile')
    StudentProfile = apps.get_model('accounts', 'StudentProfile')
    SimEvaluation = apps.get_model('fms', 'SimEvaluation')

    flight_instructor_rates = dict(
        InstructorProfile.objects.values_list(
            'user__national_id',
            'flight_instructor_hourly_rate',
        )
    )
    sim_instructor_rates = dict(
        InstructorProfile.objects.values_list(
            'user__national_id',
            'sim_instructor_hourly_rate',
        )
    )
    student_rates = dict(
        StudentProfile.objects.values_list(
            'user__national_id',
            'flight_rate',
        )
    )

    for model_name in FLIGHT_MODELS:
        model = apps.get_model('fms', model_name)
        evaluations = list(model.objects.select_related('aircraft'))
        for evaluation in evaluations:
            evaluation.hourly_rate_applied = student_rates.get(
                evaluation.student_id,
                evaluation.hourly_rate_applied,
            )
            evaluation.aircraft_rate_applied = evaluation.aircraft.hourly_rate
            evaluation.instructor_rate_applied = flight_instructor_rates.get(
                evaluation.instructor_id,
                Decimal('20.00'),
            )
        model.objects.bulk_update(
            evaluations,
            [
                'hourly_rate_applied',
                'aircraft_rate_applied',
                'instructor_rate_applied',
            ],
        )

    evaluations = list(SimEvaluation.objects.select_related('simulator'))
    for evaluation in evaluations:
        evaluation.simulator_rate_applied = (
            evaluation.simulator.hourly_rate_dual
            if evaluation.session_type == 'Dual'
            else evaluation.simulator.hourly_rate_single
        )
        evaluation.instructor_rate_applied = sim_instructor_rates.get(
            evaluation.instructor_id,
            Decimal('15.00'),
        )
    SimEvaluation.objects.bulk_update(
        evaluations,
        ['simulator_rate_applied', 'instructor_rate_applied'],
    )


class Migration(migrations.Migration):
    dependencies = [
        ('fms', '0063_external_and_report_fuel_rates'),
    ]

    operations = [
        migrations.AddField(
            model_name='simevaluation',
            name='simulator_rate_applied',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('35.00'),
                editable=False,
                max_digits=6,
                verbose_name='Tarifa de simulador aplicada ($/h)',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='simevaluation',
            name='instructor_rate_applied',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('15.00'),
                editable=False,
                max_digits=6,
                verbose_name='Tarifa de instructor aplicada ($/h)',
            ),
            preserve_default=False,
        ),
        *(
            operation
            for model_name in (
                'flightevaluation0_100',
                'flightevaluation100_120',
                'flightevaluation120_170',
            )
            for operation in (
                migrations.AddField(
                    model_name=model_name,
                    name='aircraft_rate_applied',
                    field=models.DecimalField(
                        decimal_places=2,
                        default=Decimal('130.00'),
                        editable=False,
                        max_digits=6,
                        verbose_name='Tarifa de aeronave aplicada ($/h)',
                    ),
                    preserve_default=False,
                ),
                migrations.AddField(
                    model_name=model_name,
                    name='instructor_rate_applied',
                    field=models.DecimalField(
                        decimal_places=2,
                        default=Decimal('20.00'),
                        editable=False,
                        max_digits=6,
                        verbose_name='Tarifa de instructor aplicada ($/h)',
                    ),
                    preserve_default=False,
                ),
            )
        ),
        *(
            migrations.AlterField(
                model_name=model_name,
                name='hourly_rate_applied',
                field=models.DecimalField(
                    decimal_places=2,
                    editable=False,
                    max_digits=6,
                    verbose_name='Tarifa de estudiante aplicada ($/h)',
                ),
            )
            for model_name in (
                'flightevaluation0_100',
                'flightevaluation100_120',
                'flightevaluation120_170',
            )
        ),
        migrations.RunPython(backfill_rate_snapshots, migrations.RunPython.noop),
    ]
