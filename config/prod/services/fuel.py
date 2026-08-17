from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Count, DecimalField, F, Sum

from fleet.models import Aircraft
from fms.models import (
    ExternalFlightEvaluation,
    FlightEvaluation0_100,
    FlightEvaluation100_120,
    FlightEvaluation120_170,
    FlightReport,
)


EVALUATION_MODELS = {
    '0-100': FlightEvaluation0_100,
    '100-120': FlightEvaluation100_120,
    '120-170': FlightEvaluation120_170,
}
ADDITIONAL_SOURCES = ('external', 'flight-reports')
ALL_SOURCES = (*EVALUATION_MODELS, *ADDITIONAL_SOURCES)

ZERO = Decimal('0')
USD_QUANTUM = Decimal('0.01')


@dataclass(frozen=True)
class FuelConsumptionReport:
    start_date: date
    end_date: date
    aircraft: str | None
    evaluation_types: tuple[str, ...]
    evaluation_count: int
    flight_hours: Decimal
    fuel_liters: Decimal
    fuel_cost_usd: Decimal


def get_fuel_consumed(
    *,
    start_date: date,
    end_date: date,
    evaluation_types: tuple[str, ...] | list[str] | None = None,
    aircraft_registration: str | None = None,
) -> FuelConsumptionReport:
    """Return flight hours and fuel totals for an inclusive date range."""
    _validate_dates(start_date, end_date)
    selected_types = _normalize_evaluation_types(evaluation_types)
    aircraft = _normalize_aircraft(aircraft_registration)

    evaluation_count = 0
    flight_hours = ZERO
    fuel_liters = ZERO
    fuel_cost_usd = ZERO

    for evaluation_type in (
        source for source in selected_types if source in EVALUATION_MODELS
    ):
        queryset = EVALUATION_MODELS[evaluation_type].objects.filter(
            session_date__range=(start_date, end_date),
        )
        if aircraft is not None:
            queryset = queryset.filter(aircraft__registration__iexact=aircraft)

        totals = queryset.aggregate(
            evaluation_count=Count('pk'),
            flight_hours=Sum('session_flight_hours', default=ZERO),
            fuel_liters=Sum('fuel_consumed', default=ZERO),
            fuel_cost_usd=Sum(
                F('fuel_consumed') * F('fuel_rate_applied'),
                output_field=DecimalField(max_digits=18, decimal_places=4),
                default=ZERO,
            ),
        )
        evaluation_count += totals['evaluation_count']
        flight_hours += totals['flight_hours']
        fuel_liters += totals['fuel_liters']
        fuel_cost_usd += totals['fuel_cost_usd']

    if 'external' in selected_types:
        queryset = ExternalFlightEvaluation.objects.filter(
            session_date__range=(start_date, end_date),
        )
        if aircraft is not None:
            queryset = queryset.filter(aircraft_registration__iexact=aircraft)
        totals = queryset.aggregate(
            evaluation_count=Count('pk'),
            flight_hours=Sum('session_flight_hours', default=ZERO),
            fuel_liters=Sum('fuel_consumed', default=ZERO),
            fuel_cost_usd=Sum(
                F('fuel_consumed') * F('fuel_rate_applied'),
                output_field=DecimalField(max_digits=18, decimal_places=4),
                default=ZERO,
            ),
        )
        evaluation_count += totals['evaluation_count']
        flight_hours += totals['flight_hours']
        fuel_liters += totals['fuel_liters']
        fuel_cost_usd += totals['fuel_cost_usd']

    if 'flight-reports' in selected_types:
        queryset = FlightReport.objects.filter(
            flight_date__range=(start_date, end_date),
        )
        if aircraft is not None:
            queryset = queryset.filter(aircraft__registration__iexact=aircraft)
        totals = queryset.aggregate(
            evaluation_count=Count('pk'),
            flight_hours=Sum('flight_hours', default=ZERO),
            fuel_liters=Sum('fuel_consumed', default=ZERO),
            fuel_cost_usd=Sum(
                F('fuel_consumed') * F('fuel_rate_applied'),
                output_field=DecimalField(max_digits=18, decimal_places=4),
                default=ZERO,
            ),
        )
        evaluation_count += totals['evaluation_count']
        flight_hours += totals['flight_hours']
        fuel_liters += totals['fuel_liters']
        fuel_cost_usd += totals['fuel_cost_usd']

    return FuelConsumptionReport(
        start_date=start_date,
        end_date=end_date,
        aircraft=aircraft,
        evaluation_types=selected_types,
        evaluation_count=evaluation_count,
        flight_hours=flight_hours,
        fuel_liters=fuel_liters,
        fuel_cost_usd=fuel_cost_usd.quantize(USD_QUANTUM),
    )


def _validate_dates(start_date: date, end_date: date) -> None:
    if not isinstance(start_date, date) or not isinstance(end_date, date):
        raise ValidationError('start_date and end_date must be date objects.')
    if start_date > end_date:
        raise ValidationError('start_date cannot be later than end_date.')


def _normalize_evaluation_types(
    evaluation_types: tuple[str, ...] | list[str] | None,
) -> tuple[str, ...]:
    if evaluation_types is None:
        return ALL_SOURCES

    selected = tuple(dict.fromkeys(evaluation_types))
    if not selected:
        raise ValidationError('At least one evaluation type is required.')

    invalid = set(selected) - set(ALL_SOURCES)
    if invalid:
        allowed = ', '.join(ALL_SOURCES)
        raise ValidationError(
            f"Unknown evaluation type(s): {', '.join(sorted(invalid))}. "
            f'Allowed values: {allowed}.'
        )
    return selected


def _normalize_aircraft(aircraft_registration: str | None) -> str | None:
    if aircraft_registration is None:
        return None

    registration = aircraft_registration.strip()
    if not registration or registration.casefold() == 'all':
        return None

    try:
        return Aircraft.objects.only('registration').get(
            registration__iexact=registration,
        ).registration
    except Aircraft.DoesNotExist:
        external_registration = (
            ExternalFlightEvaluation.objects.filter(
                aircraft_registration__iexact=registration,
            )
            .values_list('aircraft_registration', flat=True)
            .first()
        )
        if external_registration is not None:
            return external_registration
        raise ValidationError(
            f'Unknown aircraft registration: {aircraft_registration}.'
        )
