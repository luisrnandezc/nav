from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0047_update_flight_instructor_rates'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='flight_requests_blocked',
            field=models.BooleanField(
                default=False,
                verbose_name='Bloquear solicitudes de vuelo',
                help_text='Impide crear nuevas solicitudes de vuelo, incluso desde staff. No modifica solicitudes existentes.',
            ),
        ),
    ]
