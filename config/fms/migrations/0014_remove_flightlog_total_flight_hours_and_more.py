# Generated by Django 5.0.6 on 2024-12-29 22:53

import fms.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fms', '0013_alter_flightevaluation_session_letter'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='flightlog',
            name='total_flight_hours',
        ),
        migrations.AddField(
            model_name='flightlog',
            name='accumulated_flight_hours',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=5),
        ),
        migrations.AddField(
            model_name='flightlog',
            name='flight_date',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='flightlog',
            name='session_letter',
            field=models.CharField(blank=True, choices=[('', ''), ('A', 'A'), ('B', 'B'), ('E', 'E')], default='', max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='flightevaluation',
            name='accumulated_flight_hours',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=5),
        ),
        migrations.AlterField(
            model_name='flightevaluation',
            name='aircraft_registration',
            field=models.CharField(choices=[('YV1111', 'YV1111'), ('YV2222', 'YV2222')], default='YV1111', max_length=6),
        ),
        migrations.AlterField(
            model_name='flightevaluation',
            name='course_type',
            field=models.CharField(choices=[('PP', 'PP'), ('HVI', 'HVI'), ('PC', 'PC'), ('TLA', 'TLA')], default='PP', max_length=3),
        ),
        migrations.AlterField(
            model_name='flightevaluation',
            name='flight_rules',
            field=models.CharField(choices=[('VFR', 'VFR'), ('IFR', 'IFR'), ('DUAL', 'Dual')], default='VFR', max_length=4),
        ),
        migrations.AlterField(
            model_name='flightevaluation',
            name='instructor_license_type',
            field=models.CharField(choices=[('PC', 'PC'), ('TLA', 'TLA')], default='PC', max_length=3),
        ),
        migrations.AlterField(
            model_name='flightevaluation',
            name='notes',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='flightevaluation',
            name='session_flight_hours',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=5),
        ),
        migrations.AlterField(
            model_name='flightevaluation',
            name='session_grade',
            field=models.CharField(choices=[('S', 'S'), ('SN', 'NS'), ('NE', 'NE')], default='NE', max_length=2),
        ),
        migrations.AlterField(
            model_name='flightevaluation',
            name='session_letter',
            field=models.CharField(blank=True, choices=[('', ''), ('A', 'A'), ('B', 'B'), ('E', 'E')], default='', max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='flightevaluation',
            name='solo_flight',
            field=models.CharField(choices=[('Y', 'Y'), ('N', 'N')], default='N', max_length=3),
        ),
        migrations.AlterField(
            model_name='flightevaluation',
            name='student_license_type',
            field=models.CharField(choices=[('AP', 'AP'), ('PP', 'PP'), ('PC', 'PC'), ('TLA', 'TLA')], default='AP', max_length=3),
        ),
        migrations.AlterField(
            model_name='flightlog',
            name='aircraft_registration',
            field=models.CharField(choices=[('YV1111', 'YV1111'), ('YV2222', 'YV2222')], default='YV1111', max_length=6),
        ),
        migrations.AlterField(
            model_name='flightlog',
            name='course_type',
            field=models.CharField(choices=[('PP', 'PP'), ('HVI', 'HVI'), ('PC', 'PC'), ('TLA', 'TLA')], default='PP', max_length=3),
        ),
        migrations.AlterField(
            model_name='flightlog',
            name='flight_rules',
            field=models.CharField(choices=[('VFR', 'VFR'), ('IFR', 'IFR'), ('DUAL', 'Dual')], default='VFR', max_length=4),
        ),
        migrations.AlterField(
            model_name='flightlog',
            name='instructor_first_name',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='flightlog',
            name='instructor_last_name',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='flightlog',
            name='notes',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='flightlog',
            name='session_flight_hours',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=5),
        ),
        migrations.AlterField(
            model_name='flightlog',
            name='session_grade',
            field=models.CharField(choices=[('S', 'S'), ('SN', 'NS'), ('NE', 'NE')], default='NE', max_length=2),
        ),
        migrations.AlterField(
            model_name='flightlog',
            name='session_number',
            field=models.CharField(choices=fms.models.FlightLog.generate_choices, default='1', max_length=3),
        ),
        migrations.AlterField(
            model_name='flightlog',
            name='solo_flight',
            field=models.CharField(choices=[('Y', 'Y'), ('N', 'N')], default='Y', max_length=3),
        ),
        migrations.AlterField(
            model_name='flightlog',
            name='student_first_name',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='flightlog',
            name='student_last_name',
            field=models.CharField(default='', max_length=50),
        ),
    ]
