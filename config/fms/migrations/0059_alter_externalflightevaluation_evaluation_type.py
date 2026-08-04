from django.db import migrations, models


def normalize_removed_types(apps, schema_editor):
    ExternalFlightEvaluation = apps.get_model('fms', 'ExternalFlightEvaluation')
    ExternalFlightEvaluation.objects.exclude(
        evaluation_type__in=['MULTIMOTOR', 'OTRO']
    ).update(evaluation_type='OTRO')


class Migration(migrations.Migration):
    dependencies = [('fms', '0058_externalflightevaluation')]

    operations = [
        migrations.RunPython(normalize_removed_types, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='externalflightevaluation',
            name='evaluation_type',
            field=models.CharField(
                choices=[('MULTIMOTOR', 'Multimotor'), ('OTRO', 'Otro')],
                max_length=20,
                verbose_name='Tipo de evaluación',
            ),
        ),
    ]
