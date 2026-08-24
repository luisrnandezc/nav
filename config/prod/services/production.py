from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError

from fms.models import (
    FlightEvaluation0_100,
    FlightEvaluation100_120,
    FlightEvaluation120_170,
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

    @property
    def operating_flying_income_usd(self) -> Decimal:
        """Return flight income after instructor costs."""

        return (
            self.gross_flying_income_usd
            - self.instructor_flying_cost_usd
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
class FlightTrend:
    """Plot-ready flight-line totals grouped across the selected period."""

    grouping: str
    labels: list[str]
    flight_hours: list[Decimal]
    income_usd: list[Decimal]
    operating_income_usd: list[Decimal]
    aircraft_hours: dict[str, list[Decimal]]


@dataclass
class ProductionReport:
    """Complete production result consumed later by the panel and PDF."""

    filters: ProductionFilters
    totals: ProductionTotals
    by_aircraft: list[ProductionBreakdown]
    by_simulator: list[ProductionBreakdown]
    by_instructor: list[ProductionBreakdown]
    by_student: list[ProductionBreakdown]
    flight_trend: FlightTrend


def get_production_report(filters: ProductionFilters) -> ProductionReport:
    """Calculate totals and all required breakdowns from stored rate snapshots."""

    filters.validate()
    report_totals = ProductionTotals()
    breakdowns = {
        'aircraft': {},
        'simulator': {},
        'instructor': {},
        'student': {},
    }
    trend_totals = {}
    trend_aircraft = {}

    for model in FLIGHT_EVALUATION_MODELS:
        queryset = model.objects.filter(
            session_date__range=(filters.start_date, filters.end_date),
        ).select_related('aircraft')
        queryset = _filter_training_queryset(queryset, filters, include_aircraft=True)
        for evaluation in queryset.iterator():
            values = _flight_values(evaluation)
            report_totals.add(values)
            _add_flight_breakdowns(breakdowns, evaluation, values)
            _add_flight_trend_values(
                trend_totals,
                trend_aircraft,
                evaluation,
                values,
                filters,
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
        flight_trend=_build_flight_trend(
            filters,
            trend_totals,
            trend_aircraft,
        ),
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


def _add_flight_breakdowns(breakdowns, evaluation, values):
    """Add a training flight to its aircraft and people rows."""

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


def _add_simulator_breakdowns(breakdowns, evaluation, values):
    """Add a simulator session to its simulator and people rows."""

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


def _add_flight_trend_values(totals, aircraft, evaluation, values, filters):
    """Accumulate one training flight in its chart period and aircraft series."""

    bucket = _trend_bucket(evaluation.session_date, filters)
    totals.setdefault(bucket, ProductionTotals()).add(values)
    registration = evaluation.aircraft.registration
    aircraft.setdefault(registration, {})
    aircraft[registration].setdefault(bucket, ZERO)
    aircraft[registration][bucket] += values.flight_hours


def _build_flight_trend(filters, totals, aircraft):
    """Fill empty chart periods and return aligned flight-line series."""

    grouping, buckets = _trend_buckets(filters)
    return FlightTrend(
        grouping=grouping,
        labels=[_trend_label(bucket, grouping, filters.end_date) for bucket in buckets],
        flight_hours=[totals.get(bucket, ProductionTotals()).flight_hours for bucket in buckets],
        income_usd=[
            totals.get(bucket, ProductionTotals()).gross_flying_income_usd
            for bucket in buckets
        ],
        operating_income_usd=[
            (
                totals.get(bucket, ProductionTotals()).gross_flying_income_usd
                - totals.get(bucket, ProductionTotals()).instructor_flying_cost_usd
            ).quantize(MONEY_QUANTUM)
            for bucket in buckets
        ],
        aircraft_hours={
            registration: [values.get(bucket, ZERO) for bucket in buckets]
            for registration, values in sorted(aircraft.items())
        },
    )


def _trend_buckets(filters):
    """Return daily, weekly, or monthly bucket starts for the selected range."""

    day_count = (filters.end_date - filters.start_date).days + 1
    if day_count <= 31:
        return 'daily', [
            filters.start_date + timedelta(days=offset)
            for offset in range(day_count)
        ]
    if day_count <= 120:
        return 'weekly', [
            filters.start_date + timedelta(days=offset)
            for offset in range(0, day_count, 7)
        ]

    buckets = []
    current = filters.start_date.replace(day=1)
    final = filters.end_date.replace(day=1)
    while current <= final:
        buckets.append(current)
        current = date(
            current.year + (current.month == 12),
            1 if current.month == 12 else current.month + 1,
            1,
        )
    return 'monthly', buckets


def _trend_bucket(session_date, filters):
    """Return the chart bucket start containing one session date."""

    grouping, _ = _trend_buckets(filters)
    if grouping == 'daily':
        return session_date
    if grouping == 'weekly':
        offset = (session_date - filters.start_date).days
        return filters.start_date + timedelta(days=(offset // 7) * 7)
    return session_date.replace(day=1)


def _trend_label(bucket, grouping, end_date):
    """Format one compact Spanish chart-axis label."""

    if grouping == 'daily':
        return bucket.strftime('%d/%m')
    if grouping == 'weekly':
        bucket_end = min(bucket + timedelta(days=6), end_date)
        return f'{bucket:%d/%m} - {bucket_end:%d/%m}'
    return bucket.strftime('%m/%Y')


def _add_breakdown(group, key, label, values):
    """Create or update one row inside a breakdown group."""

    string_key = str(key)
    if string_key not in group:
        group[string_key] = ProductionBreakdown(string_key, label.strip())
    group[string_key].totals.add(values)


def _sorted_breakdowns(group):
    """Return breakdown rows in stable key order for tables and PDFs."""

    return sorted(group.values(), key=lambda item: item.key)
