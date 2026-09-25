"""Link only uniquely identifiable legacy fuel notes; never guess a flight."""
import re
from decimal import Decimal, InvalidOperation

from django.db import migrations


def link_legacy_fuel(apps, schema_editor):
    alias = schema_editor.connection.alias
    transaction_model = apps.get_model('transactions', 'StudentTransaction')
    pattern = re.compile(r'^Combustible: ([\d.]+)L - (.+?) - (.+)$')
    candidates = {}
    for kind in ('0_100', '100_120', '120_170'):
        model = apps.get_model('fms', f'FlightEvaluation{kind}')
        for flight in model.objects.using(alias).select_related('aircraft').exclude(fuel_consumed=0).iterator():
            key = (flight.student_id, flight.aircraft.registration,
                   f'{flight.instructor_first_name} {flight.instructor_last_name}', flight.fuel_consumed)
            candidates.setdefault(key, []).append((kind, flight.pk, flight.session_date))
    matches = {}
    for transaction in transaction_model.objects.using(alias).filter(
        notes__startswith='Combustible:', type='DEBITO', category='VUELO',
    ).select_related('student_profile__user').iterator():
        match = pattern.fullmatch(transaction.notes)
        if not match:
            continue
        try:
            liters = Decimal(match[1])
        except InvalidOperation:
            continue
        if liters <= 0:
            continue
        key = (transaction.student_profile.user.national_id, match[2], match[3], liters)
        flights = [flight for flight in candidates.get(key, []) if flight[2] <= transaction.date_added]
        if len(flights) == 1:
            kind, pk, _ = flights[0]
            matches.setdefault((kind, pk), []).append((transaction.pk, liters, transaction.amount / liters))
    for (kind, pk), transactions in matches.items():
        if len(transactions) == 1:
            transaction_id, liters, price = transactions[0]
            transaction_model.objects.using(alias).filter(pk=transaction_id).update(
                **{f'fuel_flight_{kind}_id': pk}, fuel_liters=liters, fuel_unit_price=price,
            )


class Migration(migrations.Migration):
    dependencies = [('transactions', '0012_link_late_fuel_to_flight')]
    operations = [migrations.RunPython(link_legacy_fuel, migrations.RunPython.noop)]
