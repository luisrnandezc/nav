"""Assemble read-only student history and statistics from two accounting sources.

``student_activity`` coordinates four steps: load transactions, group later fuel
by flight, summarize saved flights, and build the template statistics. Row
builders handle presentation; charge calculators handle money. No function in
this module saves a model or changes a student's balance.

Flight charges use saved applied rates, never today's aircraft prices. Later
fuel appears in its own transaction rather than in the original flight charge.
"""
from dataclasses import dataclass
from decimal import Decimal

from django.urls import reverse

from fms.models import FlightEvaluation0_100, FlightEvaluation100_120, FlightEvaluation120_170
from .models import StudentTransaction


FLIGHT_MODELS = (
    ('0_100', FlightEvaluation0_100),
    ('100_120', FlightEvaluation100_120),
    ('120_170', FlightEvaluation120_170),
)
DETAILED_AIRCRAFT = ('yv204e', 'yv206e')
TOTAL_FIELDS = (
    'total_flight_hours', 'total_consumed_liters',
    'total_flight_hours_dollars', 'total_fuel_cost',
)
ZERO = Decimal('0')
LITERS_PER_GALLON = Decimal('3.78541')


@dataclass(frozen=True)
class FlightCharges:
    """Amounts for one flight, separating the original charge from later fuel.

    ``original_amount`` is rounded after adding the unrounded flight and fuel
    costs, matching the original debit. Components are rounded separately for
    display. ``late_fuel_cost`` includes only confirmed linked transactions and
    must not be included in the original movement row.
    """

    original_liters: Decimal
    hourly_cost: Decimal
    original_fuel_cost: Decimal
    original_amount: Decimal
    late_fuel_cost: Decimal


def get_fuel_flight_key(transaction):
    """Return the linked flight's ``(evaluation kind, primary key)``, or None.

    The three flight tables can have overlapping primary keys, so both values
    are needed when grouping fuel. Reads foreign-key IDs without fetching the
    related flight from the database.
    """
    for kind, _ in FLIGHT_MODELS:
        flight_id = getattr(transaction, f'fuel_flight_{kind}_id')
        if flight_id:
            return kind, flight_id
    return None


def is_late_fuel_transaction(transaction):
    """Recognize new fuel snapshots and legacy generated fuel comments.

    Legacy transactions may have no flight link or liters snapshot. Their
    original ``Combustible:`` comment lets the page identify and flag them.
    """
    return transaction.fuel_liters is not None or transaction.notes.startswith('Combustible:')


def group_fuel_transactions_by_flight(transactions):
    """Map each linked flight key to its list of later fuel transactions.

    Include pending entries: their liters were entered later and should not
    move into the original charge. ``calculate_flight_charges`` separately
    decides whether their amount contributes to costs. Omit unlinked entries;
    this function never guesses which flight a transaction belongs to.
    """
    grouped = {}
    for transaction in transactions:
        flight_key = get_fuel_flight_key(transaction)
        if flight_key:
            grouped.setdefault(flight_key, []).append(transaction)
    return grouped


def student_visible_notes(notes):
    """Hide the exact demo ownership marker while keeping stored notes intact.

    The seed reset command still needs this metadata in the database. Only its
    student-facing presentation is cleaned; unrelated bracketed text is kept.
    """
    return notes.replace('[seed_fms_demo:v1]', '').strip()


def late_fuel_description(transaction, flight_key):
    """Describe linked fuel using flight date, aircraft and saved charge values.

    Build the short student-facing text for existing and new transactions without
    changing stored audit notes. Keep the available notes for legacy entries
    whose flight or fuel snapshot is missing rather than inventing charge data.
    """
    if not flight_key or transaction.fuel_liters is None or transaction.fuel_unit_price is None:
        return student_visible_notes(transaction.notes)
    kind, _ = flight_key
    flight = getattr(transaction, f'fuel_flight_{kind}')
    liters = format(transaction.fuel_liters.normalize(), 'f')
    price = format(transaction.fuel_unit_price.normalize(), 'f')
    return (
        'Combustible registrado posterior a la fecha del vuelo. '
        f'Vuelo del {flight.session_date:%d/%m/%Y} · {flight.aircraft.registration} · '
        f'{liters} L × ${price}/L = ${transaction.amount:.2f}.'
    )


def build_transaction_movement(transaction):
    """Convert one StudentTransaction into a movement dictionary for the UI.

    Retain its amount, transaction date and confirmation date; shorten fuel notes. Pending
    entries remain visible but are marked as not applied. ``flight`` supports
    filtering; ``sort`` puts transactions before automatic charges on the same
    day, with the primary key breaking ties within each source.
    """
    flight_key = get_fuel_flight_key(transaction)
    is_fuel = is_late_fuel_transaction(transaction)
    linked_flight = getattr(transaction, f'fuel_flight_{flight_key[0]}') if flight_key else None
    credit = transaction.type == StudentTransaction.CREDIT
    title = transaction.get_category_display()
    if is_fuel:
        title = 'Combustible registrado posteriormente'
    elif transaction.category == StudentTransaction.NA:
        title = 'Abono' if credit else 'Débito'
    return {
        'id': f'transaction-{transaction.pk}', 'date': transaction.date_added,
        'title': title,
        'label': 'Crédito' if credit else 'Débito', 'credit': credit,
        'amount': transaction.amount,
        'description': late_fuel_description(transaction, flight_key) if is_fuel else student_visible_notes(transaction.notes),
        'pending': not transaction.confirmed,
        'applied_date': transaction.confirmation_date if transaction.confirmed else None,
        'flight': is_fuel or transaction.category == StudentTransaction.FLIGHT,
        'fuel_flight_date': linked_flight.session_date if linked_flight else None,
        'fuel_aircraft': linked_flight.aircraft.registration if linked_flight else None,
        'url': reverse('fms:session_detail', args=flight_key) if flight_key else None,
        'sort': (transaction.date_added, 1, transaction.pk),
    }


def iter_student_flights(profile):
    """Yield ``(evaluation kind, flight)`` for every retained school flight.

    Query each school evaluation table using the student's national ID and load
    its aircraft in the same query. External flights and simulator sessions are
    excluded because they do not create automatic student flight debits.
    """
    for kind, model in FLIGHT_MODELS:
        flights = model.objects.filter(
            student_id=profile.user.national_id,
        ).select_related('aircraft')
        for flight in flights:
            yield kind, flight


def calculate_flight_charges(flight, linked_fuel_transactions):
    """Return FlightCharges for the original debit and confirmed later fuel.

    The flight's fuel quantity includes fuel entered later. Subtract linked
    transaction liters before pricing the original debit to prevent duplication;
    clamp that quantity to zero for inconsistent historical records. Use saved
    flight rates for the original charge and saved transaction amounts for later
    fuel, so subsequent price changes cannot reprice either entry.
    """
    separate_liters = sum((t.fuel_liters or ZERO for t in linked_fuel_transactions), ZERO)
    original_liters = max(ZERO, flight.fuel_consumed - separate_liters)
    unrounded_hourly_cost = flight.session_flight_hours * flight.hourly_rate_applied
    unrounded_fuel_cost = original_liters * flight.fuel_rate_applied
    return FlightCharges(
        original_liters=original_liters,
        hourly_cost=round(unrounded_hourly_cost, 2),
        original_fuel_cost=round(unrounded_fuel_cost, 2),
        original_amount=round(unrounded_hourly_cost + unrounded_fuel_cost, 2),
        late_fuel_cost=sum((t.amount for t in linked_fuel_transactions if t.confirmed), ZERO),
    )


def build_flight_movement(kind, flight, charges, linked_fuel_transactions):
    """Build the automatic debit row from already calculated FlightCharges.

    Show the original hours/fuel calculation and a link to the flight. Later
    fuel gets links to its separate movement rows; those amounts are absent
    from this row. A zero fuel quantity is shown as pending fuel, independently
    of transaction confirmation status. This function performs no accounting.
    """
    return {
        'id': f'flight-{kind}-{flight.pk}', 'date': flight.session_date,
        'title': f'Cargo por vuelo · {flight.aircraft.registration}',
        'label': 'Débito automático', 'credit': False, 'amount': charges.original_amount,
        'description': (
            f'{flight.session_flight_hours} h × ${flight.hourly_rate_applied}/h = ${charges.hourly_cost:.2f} · '
            f'Combustible: {charges.original_liters} L × ${flight.fuel_rate_applied}/L = ${charges.original_fuel_cost:.2f}'
        ),
        'pending': False, 'flight': True,
        'fuel_pending': flight.fuel_consumed == 0,
        'fuel_transactions': [
            {
                'url': reverse('transactions:student_overview') + f'?movement={t.pk}#transaction-{t.pk}',
                'date': t.date_added,
            }
            for t in linked_fuel_transactions
        ],
        'url': reverse('fms:session_detail', args=(kind, flight.pk)),
        'sort': (flight.session_date, 0, flight.pk),
    }


def summarize_student_flights(profile, fuel_by_flight):
    """Collect flight rows, per-aircraft totals and missing-fuel status.

    Match each flight with its grouped fuel transactions, calculate charges
    once, and reuse them for presentation and totals. Return ``movements``,
    ``aircraft_totals``, ``flight_cost`` and ``missing_fuel``. The combined cost
    uses rounded original debit totals; aircraft totals keep the separately
    rounded flight/fuel display components.
    """
    rows = []
    aircraft_totals = {}
    flight_cost = ZERO
    missing_fuel = False
    for kind, flight in iter_student_flights(profile):
        linked = fuel_by_flight.get((kind, flight.pk), [])
        charges = calculate_flight_charges(flight, linked)
        rows.append(build_flight_movement(kind, flight, charges, linked))
        flight_cost += charges.original_amount + charges.late_fuel_cost
        missing_fuel |= flight.fuel_consumed == 0
        totals = aircraft_totals.setdefault(
            flight.aircraft.registration.lower(), {key: ZERO for key in TOTAL_FIELDS},
        )
        totals['total_flight_hours'] += flight.session_flight_hours
        totals['total_consumed_liters'] += flight.fuel_consumed
        totals['total_flight_hours_dollars'] += charges.hourly_cost
        totals['total_fuel_cost'] += charges.original_fuel_cost + charges.late_fuel_cost
    return {
        'movements': rows, 'aircraft_totals': aircraft_totals,
        'flight_cost': flight_cost, 'missing_fuel': missing_fuel,
    }


def calculate_extra_flight_debits(transactions):
    """Sum confirmed flight-category debits without a later-fuel snapshot.

    These adjustments contribute to overall cost but are not assigned to an
    aircraft. Snapshot-backed fuel is excluded because the flight summary
    already includes it. Unlinked legacy fuel still follows this existing rule;
    the caller flags that uncertainty and suppresses the overview's USD/h figure.
    """
    return sum((
        t.amount for t in transactions
        if t.confirmed and t.type == StudentTransaction.DEBIT
        and t.category == StudentTransaction.FLIGHT and t.fuel_liters is None
    ), ZERO)


def build_detailed_statistics(aircraft_totals, total_cost):
    """Produce the flat statistics dictionary consumed by the full stats page.

    Include every school aircraft in overall totals and expose the template's
    two named aircraft sections, defaulting missing aircraft to zero. Derive
    gallons, consumption per hour and cost per hour from totals, not averages of
    flights. Aircraft with no hours receive zero rates. ``total_cost`` already
    includes confirmed adjustments supplied by the caller.
    """
    stats = {'total_cost': total_cost}
    for key in TOTAL_FIELDS:
        stats[key] = sum((totals[key] for totals in aircraft_totals.values()), ZERO)
        for aircraft in DETAILED_AIRCRAFT:
            stats[f'{key}_{aircraft}'] = aircraft_totals.get(aircraft, {}).get(key, ZERO)
    stats['total_consumed_gallons'] = stats['total_consumed_liters'] / LITERS_PER_GALLON
    for aircraft in DETAILED_AIRCRAFT:
        hours = stats[f'total_flight_hours_{aircraft}']
        liters = stats[f'total_consumed_liters_{aircraft}']
        cost = stats[f'total_flight_hours_dollars_{aircraft}'] + stats[f'total_fuel_cost_{aircraft}']
        stats[f'total_consumed_gallons_{aircraft}'] = liters / LITERS_PER_GALLON
        stats[f'fuel_rate_liters_{aircraft}'] = liters / hours if hours else ZERO
        stats[f'fuel_rate_gallons_{aircraft}'] = stats[f'fuel_rate_liters_{aircraft}'] / LITERS_PER_GALLON
        stats[f'flight_hour_cost_{aircraft}'] = cost / hours if hours else ZERO
    return stats


def student_activity(profile):
    """Return shared context for the student overview and full statistics page.

    Load transactions once, group later fuel by flight, summarize school flights,
    then add confirmed flight adjustments. Return detailed ``stats``, newest-first
    ``movements``, two weighted overview averages, and missing/unlinked fuel flags.

    Overview averages are None when no school hours exist. USD/h is also None
    when unresolved fuel could duplicate a charge. Filtering and pagination
    belong to the view. This function does not calculate or mutate the profile's
    current balance or accumulated flight-hour fields.
    """
    transactions = list(profile.transactions.select_related(
        *(f'fuel_flight_{kind}__aircraft' for kind, _ in FLIGHT_MODELS)
    ))
    fuel_by_flight = group_fuel_transactions_by_flight(transactions)
    flights = summarize_student_flights(profile, fuel_by_flight)
    total_cost = flights['flight_cost'] + calculate_extra_flight_debits(transactions)
    stats = build_detailed_statistics(flights['aircraft_totals'], total_cost)
    unresolved_fuel = any(
        is_late_fuel_transaction(t) and get_fuel_flight_key(t) is None
        for t in transactions
    )
    rows = [build_transaction_movement(t) for t in transactions] + flights['movements']
    hours = stats['total_flight_hours']
    liters = stats['total_consumed_liters']
    return {
        'stats': stats,
        'movements': sorted(rows, key=lambda row: row['sort'], reverse=True),
        'liters_per_hour': liters / hours if hours else None,
        'dollars_per_hour': total_cost / hours if hours and not unresolved_fuel else None,
        'missing_fuel': flights['missing_fuel'],
        'unresolved_fuel': unresolved_fuel,
    }
