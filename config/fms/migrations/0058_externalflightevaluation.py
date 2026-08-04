from django.db import migrations, models
import django.core.validators
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [('fms', '0057_alter_flightevaluation0_100_comments_and_more')]

    operations = [
        migrations.CreateModel(
            name='ExternalFlightEvaluation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instructor_id', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1000000), django.core.validators.MaxValueValidator(99999999)], verbose_name='ID instructor')),
                ('instructor_first_name', models.CharField(max_length=50, verbose_name='Nombre')),
                ('instructor_last_name', models.CharField(max_length=50, verbose_name='Apellido')),
                ('instructor_license_type', models.CharField(choices=[('PCA', 'PCA'), ('TLA', 'TLA')], default='PCA', max_length=3, verbose_name='Tipo de licencia')),
                ('instructor_license_number', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1000000), django.core.validators.MaxValueValidator(99999999)], verbose_name='Número de licencia')),
                ('student_id', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1000000), django.core.validators.MaxValueValidator(99999999)], verbose_name='ID alumno')),
                ('student_first_name', models.CharField(max_length=50, verbose_name='Nombre')),
                ('student_last_name', models.CharField(max_length=50, verbose_name='Apellido')),
                ('student_license_type', models.CharField(choices=[('AP', 'AP'), ('PPA', 'PPA'), ('PCA', 'PCA'), ('TLA', 'TLA')], max_length=3, verbose_name='Tipo de licencia')),
                ('student_license_number', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1000000), django.core.validators.MaxValueValidator(99999999)], verbose_name='Número de licencia')),
                ('course_type', models.CharField(choices=[('N/A', 'No inscrito'), ('PPA-T', 'PPA-T'), ('PPA-P', 'PPA-P'), ('HVI-T', 'HVI-T'), ('HVI-P', 'HVI-P'), ('PCA-T', 'PCA-T'), ('PCA-P', 'PCA-P'), ('IVA-T', 'IVA-T'), ('IVA-P', 'IVA-P'), ('IVS-T', 'IVS-T'), ('IVS-P', 'IVS-P'), ('RCL', 'RCL')], default='PCA-P', max_length=10, verbose_name='Tipo de curso')),
                ('evaluation_type', models.CharField(choices=[('RECALIFICACION', 'Recalificación'), ('MULTIMOTOR', 'Multimotor'), ('CHEQUEO', 'Chequeo')], max_length=20, verbose_name='Tipo de evaluación')),
                ('session_date', models.DateField(default=django.utils.timezone.now, verbose_name='Fecha')),
                ('flight_rules', models.CharField(choices=[('VFR', 'VFR'), ('IFR', 'IFR'), ('DUAL', 'Dual')], default='VFR', max_length=4, verbose_name='Reglas de vuelo')),
                ('solo_flight', models.CharField(choices=[('NO', 'NO'), ('SI', 'SI')], default='NO', max_length=3, verbose_name='Vuelo solo')),
                ('session_number', models.CharField(choices=[(str(i), str(i)) for i in range(1, 34)], default='1', max_length=3, verbose_name='Número')),
                ('session_letter', models.CharField(blank=True, choices=[('', ''), ('A', 'A'), ('B', 'B'), ('C', 'C')], default='', max_length=1, verbose_name='Repetición de la sesión')),
                ('accumulated_flight_hours', models.DecimalField(decimal_places=1, default=0, max_digits=5, verbose_name='Horas de vuelo acumuladas')),
                ('initial_hourmeter', models.DecimalField(decimal_places=1, default=0, max_digits=6, verbose_name='Horómetro inicial')),
                ('final_hourmeter', models.DecimalField(decimal_places=1, default=0, max_digits=6, verbose_name='Horómetro final')),
                ('fuel_consumed', models.DecimalField(decimal_places=1, default=0, max_digits=4, verbose_name='Combustible consumido (litros)')),
                ('session_flight_hours', models.DecimalField(decimal_places=1, default=0, max_digits=3, verbose_name='Horas sesión')),
                ('aircraft_registration', models.CharField(max_length=20, verbose_name='Matrícula de aeronave')),
                ('session_grade', models.CharField(choices=[('SS', 'SS'), ('S', 'S'), ('NS', 'NS'), ('NE', 'NE')], default='S', max_length=2, verbose_name='Nota')),
                ('grades', models.JSONField(default=dict, verbose_name='Calificaciones detalladas')),
                ('comments', models.TextField(blank=True, validators=[django.core.validators.MinLengthValidator(15), django.core.validators.MaxLengthValidator(1000)], verbose_name='Comentarios')),
            ],
            options={'verbose_name': 'Evaluación externa', 'verbose_name_plural': 'Evaluaciones externas', 'ordering': ['-session_date', '-id']},
        ),
    ]
