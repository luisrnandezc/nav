"""Accounting operations shared by web views and local demo-data commands."""
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import StudentProfile
from .models import StudentTransaction


def flight_link_kwargs(evaluation):
    """Return the polymorphic flight link field for a school evaluation."""
    model_name = type(evaluation)._meta.model_name
    kind = model_name.removeprefix('flightevaluation')
    field_name = f'fuel_flight_{kind}'
    if not hasattr(StudentTransaction, f'{field_name}_id'):
        raise ValidationError('El tipo de evaluación no admite movimientos contables.')
    return {field_name: evaluation}


def signed_movement_type(delta):
    """Return debit for a positive charge delta and credit for a negative one."""
    return StudentTransaction.DEBIT if delta > 0 else StudentTransaction.CREDIT


def decimal_label(value):
    """Format a Decimal without unnecessary trailing zeroes for audit notes."""
    return format(Decimal(value).normalize(), 'f')


def create_flight_adjustment(
    *, profile, evaluation, amount, movement_type, activity_type, actor,
    notes, recorded_at, fuel_liters=None, flight_hours=None,
):
    """Create one confirmed, flight-linked adjustment that applies its balance effect."""
    return StudentTransaction.objects.create(
        student_profile=profile,
        amount=amount,
        type=movement_type,
        category=StudentTransaction.FLIGHT,
        date_added=recorded_at.date(),
        added_by=actor,
        confirmed=True,
        confirmed_by=actor,
        confirmation_date=recorded_at,
        fuel_liters=fuel_liters,
        fuel_unit_price=evaluation.fuel_rate_applied if fuel_liters is not None else None,
        flight_hours=flight_hours,
        flight_activity_type=activity_type,
        notes=notes,
        **flight_link_kwargs(evaluation),
    )


@transaction.atomic
def record_flight_corrections(original, corrected, actor=None, recorded_at=None):
    """Record admin changes to flight hours and fuel as confirmed adjustments.

    The corrected evaluation must already be saved inside the caller's atomic
    operation. Each changed component creates its own immutable movement using
    the rates captured by the original flight. Creating the transactions is the
    only operation here that changes the student's balance.
    """
    if type(original) is not type(corrected) or original.pk != corrected.pk:
        raise ValidationError('La evaluación original y la corregida no coinciden.')

    recorded_at = recorded_at or timezone.now()
    profile = StudentProfile.objects.select_for_update().get(
        user__national_id=original.student_id,
    )
    common = (
        f'Vuelo del {original.session_date:%d/%m/%Y} · '
        f'{original.aircraft.registration} · Sesión {original.session_number}.'
    )
    movements = []

    hours_delta = corrected.session_flight_hours - original.session_flight_hours
    if hours_delta:
        amount = round(abs(hours_delta) * original.hourly_rate_applied, 2)
        notes = (
            f'Corrección de tiempo de vuelo. {common} '
            f'{decimal_label(original.session_flight_hours)} h → '
            f'{decimal_label(corrected.session_flight_hours)} h · '
            f'{decimal_label(abs(hours_delta))} h × '
            f'${decimal_label(original.hourly_rate_applied)}/h = ${amount:.2f}.'
        )
        movements.append(create_flight_adjustment(
            profile=profile,
            evaluation=corrected,
            amount=amount,
            movement_type=signed_movement_type(hours_delta),
            activity_type=StudentTransaction.HOURS_CORRECTION,
            actor=actor,
            notes=notes,
            recorded_at=recorded_at,
            flight_hours=abs(hours_delta),
        ))

    fuel_delta = corrected.fuel_consumed - original.fuel_consumed
    if fuel_delta:
        amount = round(abs(fuel_delta) * original.fuel_rate_applied, 2)
        notes = (
            f'Corrección de combustible. {common} '
            f'{decimal_label(original.fuel_consumed)} L → '
            f'{decimal_label(corrected.fuel_consumed)} L · '
            f'{decimal_label(abs(fuel_delta))} L × '
            f'${decimal_label(original.fuel_rate_applied)}/L = ${amount:.2f}.'
        )
        movements.append(create_flight_adjustment(
            profile=profile,
            evaluation=corrected,
            amount=amount,
            movement_type=signed_movement_type(fuel_delta),
            activity_type=StudentTransaction.FUEL_CORRECTION,
            actor=actor,
            notes=notes,
            recorded_at=recorded_at,
            fuel_liters=abs(fuel_delta),
        ))

    return movements


@transaction.atomic
def record_late_fuel(model_class, evaluation_id, liters, staff, observations='', recorded_at=None):
    """Record missing fuel and its confirmed debit as one atomic operation.

    Lock the flight and student before changing quantities or balance. Preserve
    the flight reference and applied fuel price in the transaction. ``recorded_at``
    defaults to now; callers seeding historical examples may supply a timestamp.
    The caller is responsible for authorizing the staff member's access.
    """
    try:
        liters = Decimal(liters)
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError('El volumen de combustible debe ser un número válido.')
    if (not liters.is_finite() or not Decimal('0.1') <= liters <= 1000
            or liters != liters.quantize(Decimal('0.1'))):
        raise ValidationError('Ingrese entre 0.1 y 1000 litros, con un decimal como máximo.')
    evaluation = model_class.objects.select_for_update().select_related('aircraft').get(pk=evaluation_id)
    if evaluation.fuel_consumed != 0:
        raise ValidationError(f'Esta evaluación ya tiene combustible especificado: {evaluation.fuel_consumed} litros.')
    profile = StudentProfile.objects.select_for_update().get(user__national_id=evaluation.student_id)
    aircraft = evaluation.aircraft
    amount = round(liters * aircraft.fuel_cost, 2)
    recorded_at = recorded_at or timezone.now()
    model_type = model_class._meta.model_name
    notes = (
        f'Combustible registrado posteriormente. '
        f'Vuelo del {evaluation.session_date:%d/%m/%Y} · {aircraft.registration} · '
        f'{evaluation.session_flight_hours} h · Sesión {evaluation.session_number}. '
        f'Instructor: {evaluation.instructor_first_name} {evaluation.instructor_last_name}. '
        f'Referencia: {model_type} #{evaluation.pk}. '
        f'{liters} L × ${aircraft.fuel_cost}/L = ${amount}. '
    )
    if observations.strip():
        notes += f'Observaciones: {observations.strip()[:1000]}'
    model_class.objects.filter(pk=evaluation_id).update(fuel_consumed=liters)
    return StudentTransaction.objects.create(
        student_profile=profile, amount=amount, type=StudentTransaction.DEBIT,
        category=StudentTransaction.FLIGHT, date_added=recorded_at.date(),
        added_by=staff, confirmed=True, confirmed_by=staff, confirmation_date=recorded_at,
        fuel_liters=liters, fuel_unit_price=aircraft.fuel_cost, notes=notes,
        flight_activity_type=StudentTransaction.LATE_FUEL,
        **{f'fuel_flight_{model_type.removeprefix("flightevaluation")}': evaluation},
    )
