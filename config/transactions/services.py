"""Accounting operations shared by web views and local demo-data commands."""
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import StudentProfile
from .models import StudentTransaction


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
        **{f'fuel_flight_{model_type.removeprefix("flightevaluation")}': evaluation},
    )
