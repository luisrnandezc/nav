# config/fms/migrations/0043_remove_log_models.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('fms', '0042_flightevaluation100_120_final_hourmeter_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='SimulatorLog',
        ),
        migrations.DeleteModel(
            name='FlightLog',
        ),
    ]