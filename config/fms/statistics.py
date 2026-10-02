"""Shared read-only calculations for student flight statistics."""
from decimal import Decimal

from django.db.models import Sum

from .models import FlightEvaluation0_100, FlightEvaluation100_120, FlightEvaluation120_170


FLIGHT_MODELS = (
    FlightEvaluation0_100,
    FlightEvaluation100_120,
    FlightEvaluation120_170,
)
DETAILED_AIRCRAFT = ('yv204e', 'yv206e')
LITERS_PER_GALLON = Decimal('3.78541')
ZERO = Decimal('0')


def calculate_student_stats(profile):
    """Calculate current NAV flight statistics directly from evaluations.

    Aggregate the current flight hours and fuel quantities saved in every school
    evaluation table. Each flight's cost uses the hour and fuel rates captured
    on that evaluation, so later changes to student or aircraft prices do not
    rewrite historical statistics. Manual balance transactions never enter these
    totals. Late-fuel entries and admin corrections are reflected through the
    evaluation fields they update; their ledger transactions are not added again.
    """
    aircraft_totals = {}
    for model in FLIGHT_MODELS:
        rows = model.objects.filter(student_id=profile.user.national_id).values(
            'aircraft__registration',
            'hourly_rate_applied',
            'fuel_rate_applied',
        ).annotate(
            hours=Sum('session_flight_hours'),
            liters=Sum('fuel_consumed'),
        )
        for row in rows:
            registration = row['aircraft__registration'].lower()
            totals = aircraft_totals.setdefault(registration, {
                'hours': ZERO,
                'liters': ZERO,
                'hours_cost': ZERO,
                'fuel_cost': ZERO,
            })
            hours = row['hours'] or ZERO
            liters = row['liters'] or ZERO
            totals['hours'] += hours
            totals['liters'] += liters
            totals['hours_cost'] += hours * row['hourly_rate_applied']
            totals['fuel_cost'] += liters * row['fuel_rate_applied']

    stats = {}
    total_hours = ZERO
    total_liters = ZERO
    total_hours_cost = ZERO
    total_fuel_cost = ZERO
    for totals in aircraft_totals.values():
        total_hours += totals['hours']
        total_liters += totals['liters']
        total_hours_cost += totals['hours_cost']
        total_fuel_cost += totals['fuel_cost']

    stats.update({
        'total_flight_hours': total_hours,
        'total_flight_hours_dollars': total_hours_cost,
        'total_consumed_liters': total_liters,
        'total_consumed_gallons': total_liters / LITERS_PER_GALLON,
        'total_fuel_cost': total_fuel_cost,
        'total_cost': total_hours_cost + total_fuel_cost,
        'fuel_rate_liters': total_liters / total_hours if total_hours else ZERO,
        'flight_hour_cost': (
            (total_hours_cost + total_fuel_cost) / total_hours if total_hours else ZERO
        ),
    })

    for aircraft in DETAILED_AIRCRAFT:
        totals = aircraft_totals.get(aircraft, {
            'hours': ZERO,
            'liters': ZERO,
            'hours_cost': ZERO,
            'fuel_cost': ZERO,
        })
        hours = totals['hours']
        liters = totals['liters']
        hours_cost = totals['hours_cost']
        fuel_cost = totals['fuel_cost']
        gallons = liters / LITERS_PER_GALLON
        stats.update({
            f'total_flight_hours_{aircraft}': hours,
            f'total_flight_hours_dollars_{aircraft}': hours_cost,
            f'total_consumed_liters_{aircraft}': liters,
            f'total_consumed_gallons_{aircraft}': gallons,
            f'total_fuel_cost_{aircraft}': fuel_cost,
            f'fuel_rate_liters_{aircraft}': liters / hours if hours else ZERO,
            f'fuel_rate_gallons_{aircraft}': gallons / hours if hours else ZERO,
            f'fuel_hour_cost_{aircraft}': fuel_cost / hours if hours else ZERO,
            f'flight_hour_cost_{aircraft}': (
                (hours_cost + fuel_cost) / hours if hours else ZERO
            ),
        })

    return stats
