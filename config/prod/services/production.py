from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError

from fms.models import (
    ExternalFlightEvaluation,
    FlightEvaluation0_100,
    FlightEvaluation100_120,
    FlightEvaluation120_170,
    FlightReport,
    SimEvaluation,
)


FLIGHT_EVALUATION_MODELS = (
    FlightEvaluation0_100,
    FlightEvaluation100_120,
    FlightEvaluation120_170,
)
ZERO = Decimal('0')
MONEY_QUANTUM = Decimal('0.01')


@dataclass(frozen=True)
class ProductionFilters:
    """Validated date and optional entity filters for one production report."""

    start_date: date
    end_date: date
    aircraft_registrations: tuple[str, ...] = ()
    simulator_ids: tuple[int, ...] = ()
    instructor_ids: tuple[int, ...] = ()
    student_ids: tuple[int, ...] = ()

    def validate(self) -> None:
        """Reject invalid date values before any database queries run."""

        if not isinstance(self.start_date, date) or not isinstance(self.end_date, date):
            raise ValidationError('start_date and end_date must be date objects.')
        if self.start_date > self.end_date:
            raise ValidationError('start_date cannot be later than end_date.')


@dataclass
class ProductionTotals:
    """Numeric production totals shared by the report and its breakdown rows."""

    fuel_liters: Decimal = ZERO
    fuel_cost_usd: Decimal = ZERO
    flight_hours: Decimal = ZERO
    gross_flying_income_usd: Decimal = ZERO
    instructor_flying_cost_usd: Decimal = ZERO
    net_flying_revenue_usd: Decimal = ZERO
    student_flying_value_usd: Decimal = ZERO
    simulator_hours: Decimal = ZERO
    gross_simulator_income_usd: Decimal = ZERO
    instructor_simulator_cost_usd: Decimal = ZERO
    net_simulator_revenue_usd: Decimal = ZERO

    @property
    def instructor_production_usd(self) -> Decimal:
        """Return combined flight and simulator instructor compensation."""

        return (
            self.instructor_flying_cost_usd
            + self.instructor_simulator_cost_usd
        ).quantize(MONEY_QUANTUM)

    def add(self, other: 'ProductionTotals') -> None:
        """Add another set of production values into this accumulator."""

        for field_name in self.__dataclass_fields__:
            setattr(self, field_name, getattr(self, field_name) + getattr(other, field_name))

    def round_money(self) -> None:
        """Round every USD total to cents after all records are accumulated."""

        for field_name in self.__dataclass_fields__:
            if field_name.endswith('_usd'):
                setattr(self, field_name, getattr(self, field_name).quantize(MONEY_QUANTUM))


@dataclass
class ProductionBreakdown:
    """Totals for one aircraft, simulator, person, or calendar date."""

    key: str
    label: str
    totals: ProductionTotals = field(default_factory=ProductionTotals)


@dataclass
class ProductionReport:
    """Complete production result consumed later by the panel and PDF."""

    filters: ProductionFilters
    totals: ProductionTotals
    by_aircraft: list[ProductionBreakdown]
    by_simulator: list[ProductionBreakdown]
    by_instructor: list[ProductionBreakdown]
    by_student: list[ProductionBreakdown]
    by_date: list[ProductionBreakdown]


def get_production_report(filters: ProductionFilters) -> ProductionReport:
    """Calculate totals and all required breakdowns from stored rate snapshots."""

    filters.validate()
    report_totals = ProductionTotals()
    breakdowns = {
        'aircraft': {},
        'simulator': {},
        'instructor': {},
        'student': {},
        'date': {},
    }

    for model in FLIGHT_EVALUATION_MODELS:
        queryset = model.objects.filter(
            session_date__range=(filters.start_date, filters.end_date),
        ).select_related('aircraft')
        queryset = _filter_training_queryset(queryset, filters, include_aircraft=True)
        for evaluation in queryset.iterator():
            values = _flight_values(evaluation)
            report_totals.add(values)
            _add_flight_breakdowns(breakdowns, evaluation, values)

    external_queryset = ExternalFlightEvaluation.objects.filter(
        session_date__range=(filters.start_date, filters.end_date),
    )
    if filters.aircraft_registrations:
        external_queryset = external_queryset.filter(
            aircraft_registration__in=filters.aircraft_registrations,
        )
    if filters.instructor_ids:
        external_queryset = external_queryset.filter(instructor_id__in=filters.instructor_ids)
    if filters.student_ids:
        external_queryset = external_queryset.filter(student_id__in=filters.student_ids)
    for evaluation in external_queryset.iterator():
        values = _fuel_values(evaluation)
        report_totals.add(values)
        _add_fuel_breakdowns(
            breakdowns,
            evaluation.session_date,
            evaluation.aircraft_registration,
            values,
            instructor=(
                evaluation.instructor_id,
                f'{evaluation.instructor_first_name} {evaluation.instructor_last_name}',
            ),
            student=(
                evaluation.student_id,
                f'{evaluation.student_first_name} {evaluation.student_last_name}',
            ),
        )

    report_queryset = FlightReport.objects.filter(
        flight_date__range=(filters.start_date, filters.end_date),
    ).select_related('aircraft')
    if filters.aircraft_registrations:
        report_queryset = report_queryset.filter(
            aircraft__registration__in=filters.aircraft_registrations,
        )
    if filters.instructor_ids or filters.student_ids:
        report_queryset = report_queryset.none()
    for flight_report in report_queryset.iterator():
        values = _fuel_values(flight_report)
        report_totals.add(values)
        _add_fuel_breakdowns(
            breakdowns,
            flight_report.flight_date,
            flight_report.aircraft.registration,
            values,
        )

    sim_queryset = SimEvaluation.objects.filter(
        session_date__range=(filters.start_date, filters.end_date),
    ).select_related('simulator')
    sim_queryset = _filter_training_queryset(sim_queryset, filters)
    if filters.simulator_ids:
        sim_queryset = sim_queryset.filter(simulator_id__in=filters.simulator_ids)
    for evaluation in sim_queryset.iterator():
        values = _simulator_values(evaluation)
        report_totals.add(values)
        _add_simulator_breakdowns(breakdowns, evaluation, values)

    report_totals.round_money()
    for group in breakdowns.values():
        for breakdown in group.values():
            breakdown.totals.round_money()

    return ProductionReport(
        filters=filters,
        totals=report_totals,
        by_aircraft=_sorted_breakdowns(breakdowns['aircraft']),
        by_simulator=_sorted_breakdowns(breakdowns['simulator']),
        by_instructor=_sorted_breakdowns(breakdowns['instructor']),
        by_student=_sorted_breakdowns(breakdowns['student']),
        by_date=_sorted_breakdowns(breakdowns['date']),
    )


def _filter_training_queryset(queryset, filters, *, include_aircraft=False):
    """Apply the filters shared by flight and simulator training sessions."""

    if include_aircraft and filters.aircraft_registrations:
        queryset = queryset.filter(
            aircraft__registration__in=filters.aircraft_registrations,
        )
    if filters.instructor_ids:
        queryset = queryset.filter(instructor_id__in=filters.instructor_ids)
    if filters.student_ids:
        queryset = queryset.filter(student_id__in=filters.student_ids)
    return queryset


def _flight_values(evaluation) -> ProductionTotals:
    """Calculate production values contributed by one training flight."""

    hours = evaluation.session_flight_hours
    gross_income = hours * evaluation.aircraft_rate_applied
    instructor_cost = hours * evaluation.instructor_rate_applied
    return ProductionTotals(
        fuel_liters=evaluation.fuel_consumed,
        fuel_cost_usd=evaluation.fuel_consumed * evaluation.fuel_rate_applied,
        flight_hours=hours,
        gross_flying_income_usd=gross_income,
        instructor_flying_cost_usd=instructor_cost,
        net_flying_revenue_usd=gross_income - instructor_cost,
        student_flying_value_usd=hours * evaluation.hourly_rate_applied,
    )


def _simulator_values(evaluation) -> ProductionTotals:
    """Calculate production values contributed by one simulator session."""

    hours = evaluation.session_sim_hours
    gross_income = hours * evaluation.simulator_rate_applied
    instructor_cost = hours * evaluation.instructor_rate_applied
    return ProductionTotals(
        simulator_hours=hours,
        gross_simulator_income_usd=gross_income,
        instructor_simulator_cost_usd=instructor_cost,
        net_simulator_revenue_usd=gross_income - instructor_cost,
    )


def _fuel_values(record) -> ProductionTotals:
    """Calculate the fuel-only contribution of an external flight or report."""

    return ProductionTotals(
        fuel_liters=record.fuel_consumed,
        fuel_cost_usd=record.fuel_consumed * record.fuel_rate_applied,
    )


def _add_flight_breakdowns(breakdowns, evaluation, values):
    """Add a training flight to its aircraft, people, and date rows."""

    _add_breakdown(
        breakdowns['aircraft'],
        evaluation.aircraft.registration,
        evaluation.aircraft.registration,
        values,
    )
    _add_breakdown(
        breakdowns['instructor'],
        evaluation.instructor_id,
        f'{evaluation.instructor_first_name} {evaluation.instructor_last_name}',
        values,
    )
    _add_breakdown(
        breakdowns['student'],
        evaluation.student_id,
        f'{evaluation.student_first_name} {evaluation.student_last_name}',
        values,
    )
    _add_date_breakdown(breakdowns, evaluation.session_date, values)


def _add_simulator_breakdowns(breakdowns, evaluation, values):
    """Add a simulator session to its simulator, people, and date rows."""

    _add_breakdown(
        breakdowns['simulator'],
        evaluation.simulator_id,
        evaluation.simulator.name,
        values,
    )
    _add_breakdown(
        breakdowns['instructor'],
        evaluation.instructor_id,
        f'{evaluation.instructor_first_name} {evaluation.instructor_last_name}',
        values,
    )
    _add_breakdown(
        breakdowns['student'],
        evaluation.student_id,
        f'{evaluation.student_first_name} {evaluation.student_last_name}',
        values,
    )
    _add_date_breakdown(breakdowns, evaluation.session_date, values)


def _add_fuel_breakdowns(
    breakdowns,
    session_date,
    aircraft_registration,
    values,
    *,
    instructor=None,
    student=None,
):
    """Add fuel-only activity to every breakdown with known identifying data."""

    _add_breakdown(
        breakdowns['aircraft'],
        aircraft_registration,
        aircraft_registration,
        values,
    )
    if instructor:
        _add_breakdown(breakdowns['instructor'], instructor[0], instructor[1], values)
    if student:
        _add_breakdown(breakdowns['student'], student[0], student[1], values)
    _add_date_breakdown(breakdowns, session_date, values)


def _add_date_breakdown(breakdowns, session_date, values):
    """Add production values to the row for a calendar date."""

    _add_breakdown(
        breakdowns['date'],
        session_date.isoformat(),
        session_date.isoformat(),
        values,
    )


def _add_breakdown(group, key, label, values):
    """Create or update one row inside a breakdown group."""

    string_key = str(key)
    if string_key not in group:
        group[string_key] = ProductionBreakdown(string_key, label.strip())
    group[string_key].totals.add(values)


def _sorted_breakdowns(group):
    """Return breakdown rows in stable key order for tables and PDFs."""

    return sorted(group.values(), key=lambda item: item.key)
