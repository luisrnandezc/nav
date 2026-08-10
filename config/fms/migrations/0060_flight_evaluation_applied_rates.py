from django.db import migrations, models


EVALUATION_MODELS = (
    'FlightEvaluation0_100',
    'FlightEvaluation100_120',
    'FlightEvaluation120_170',
)


def backfill_applied_rates(apps, schema_editor):
    for model_name in EVALUATION_MODELS:
        evaluation_model = apps.get_model('fms', model_name)
        for evaluation in evaluation_model.objects.select_related('aircraft').iterator():
            evaluation.hourly_rate_applied = evaluation.aircraft.hourly_rate
            evaluation.fuel_rate_applied = evaluation.aircraft.fuel_cost
            evaluation.save(
                update_fields=['hourly_rate_applied', 'fuel_rate_applied']
            )


class Migration(migrations.Migration):
    dependencies = [('fms', '0059_alter_externalflightevaluation_evaluation_type')]

    operations = [
        *(
            migrations.AddField(
                model_name=model_name.lower(),
                name=field_name,
                field=models.DecimalField(
                    decimal_places=2,
                    default=0,
                    editable=False,
                    max_digits=6,
                    verbose_name=verbose_name,
                ),
                preserve_default=False,
            )
            for model_name in EVALUATION_MODELS
            for field_name, verbose_name in (
                ('hourly_rate_applied', 'Tarifa de vuelo aplicada ($/h)'),
                ('fuel_rate_applied', 'Tarifa de combustible aplicada ($/litro)'),
            )
        ),
        migrations.RunPython(backfill_applied_rates, migrations.RunPython.noop),
    ]
