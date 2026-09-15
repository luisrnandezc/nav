from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('sms', '0028_risk_post_evaluation_justification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='riskevaluationreport',
            name='registration_date',
            field=models.DateField(
                default=django.utils.timezone.localdate,
                verbose_name='Fecha de registro',
            ),
        ),
    ]
