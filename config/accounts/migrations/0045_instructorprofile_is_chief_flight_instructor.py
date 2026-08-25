from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0044_staffprofile_production_permission'),
    ]

    operations = [
        migrations.AddField(
            model_name='instructorprofile',
            name='is_chief_flight_instructor',
            field=models.BooleanField(
                default=False,
                verbose_name='Jefe de instructores de vuelo',
            ),
        ),
    ]
