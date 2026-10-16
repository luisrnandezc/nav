"""FPT backend actions, using the Scheduler's Django forms/JSON conventions."""

import json
from datetime import timedelta
from functools import wraps

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, OperationalError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .fpt_forms import FPTPeriodForm, FPTSessionForm
from .models import FPTPeriod, FPTSession
from .permissions import can_manage_fpt_schedule, can_view_fpt_schedule


def fpt_access(*, manage=False):
    """Authorize before lookup and translate expected failures after rollback."""
    def decorate(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            policy = can_manage_fpt_schedule if manage or request.method == 'POST' else can_view_fpt_schedule
            if not policy(request.user):
                return JsonResponse({'error': 'Acceso denegado'}, status=403)
            try:
                return view(request, *args, **kwargs)
            except ValidationError as exc:
                errors = exc.message_dict if hasattr(exc, 'message_dict') else {'__all__': exc.messages}
                return JsonResponse({'error': 'Revise los datos de la solicitud.', 'errors': errors}, status=400)
            except ProtectedError:
                return JsonResponse({'error': 'El periodo tiene sesiones. Elimínelas primero.'}, status=409)
            except IntegrityError:
                return occupancy_conflict()
            except OperationalError as exc:
                # SQLite may reject a concurrent writer before checking overlap.
                # Other database failures must remain visible as server errors.
                if connection.vendor == 'sqlite' and 'locked' in str(exc).lower():
                    return occupancy_conflict()
                raise
        return wrapped
    return decorate


def occupancy_conflict():
    return JsonResponse({
        'error': 'El horario o periodo cambió o ya está ocupado. Actualice el calendario e intente de nuevo.',
    }, status=409)


def request_data(request):
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except (ValueError, UnicodeDecodeError):
            raise ValidationError('El cuerpo debe contener JSON válido.')
        if not isinstance(data, dict):
            raise ValidationError('El cuerpo JSON debe ser un objeto.')
    elif request.content_type in ('application/x-www-form-urlencoded', 'multipart/form-data'):
        data = request.POST.dict()
        data.pop('csrfmiddlewaretoken', None)
    else:
        raise ValidationError('Use JSON o datos de formulario.')
    if any(isinstance(value, (list, dict)) for value in data.values()):
        raise ValidationError('Los campos deben contener valores simples.')
    return data


def save_form(form_class, data, instance=None):
    """POST edits merge only explicit fields into the freshly locked instance."""
    fields = form_class._meta.fields
    unknown = set(data) - set(fields)
    if unknown:
        raise ValidationError('La solicitud contiene campos no admitidos.')
    values = model_to_dict(instance, fields=fields) if instance is not None else {}
    values.update(data)
    form = form_class(values, instance=instance)
    if not form.is_valid():
        raise ValidationError({field: list(errors) for field, errors in form.errors.items()})
    # save() revalidates after form validation; the model/database remains the
    # final authority if a competing request changes occupancy in between.
    return form.save()


def period_data(period):
    return {
        'id': period.pk, 'start_date': period.start_date.isoformat(),
        'end_date': period.end_date.isoformat(), 'is_active': period.is_active,
    }


def participant_name(user, external):
    return (user.get_full_name() or user.username) if user else external


def session_data(session):
    return {
        'id': session.pk, 'period': session.period_id, 'date': session.date.isoformat(),
        'start_hour': session.start_hour, 'start_time': session.start_time.strftime('%H:%M'),
        'end_time': session.end_time.strftime('%H:%M'), 'status': session.status,
        'status_label': session.get_status_display(),
        'student': session.student_id, 'external_student_name': session.external_student_name,
        'student_name': participant_name(session.student, session.external_student_name),
        'instructor': session.instructor_id, 'external_instructor_name': session.external_instructor_name,
        'instructor_name': participant_name(session.instructor, session.external_instructor_name),
        'category': session.category, 'category_label': session.get_category_display(),
        'notes': session.notes,
    }


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
@fpt_access()
def periods(request):
    if request.method == 'POST':
        data = request_data(request)
        with transaction.atomic():
            period = save_form(FPTPeriodForm, data)
        return JsonResponse({'success': True, 'period': period_data(period)}, status=201)
    return JsonResponse({
        'periods': [period_data(period) for period in FPTPeriod.objects.all()],
        'can_manage': can_manage_fpt_schedule(request.user),
        'categories': [{'value': value, 'label': label} for value, label in FPTSession.Category.choices],
        'statuses': [{'value': value, 'label': label} for value, label in FPTSession.Status.choices],
    })


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
@fpt_access()
def period_detail(request, period_id):
    if request.method == 'POST':
        data = request_data(request)
        with transaction.atomic():
            period = get_object_or_404(FPTPeriod.objects.select_for_update(), pk=period_id)
            period = save_form(FPTPeriodForm, data, instance=period)
        return JsonResponse({'success': True, 'period': period_data(period)})

    period = get_object_or_404(FPTPeriod, pk=period_id)
    sessions = list(period.sessions.select_related('student', 'instructor'))
    occupied = {}
    for session in sessions:
        occupied.setdefault(session.date, []).append(session.start_hour)
    days = []
    day = period.start_date
    while day <= period.end_date:
        free = [hour for hour in range(8, 19) if not any(
            start < hour + 2 and start + 2 > hour for start in occupied.get(day, [])
        )] if period.is_active else []
        days.append({'date': day.isoformat(), 'available_start_hours': free})
        day += timedelta(days=1)
    return JsonResponse({
        'period': period_data(period), 'sessions': [session_data(session) for session in sessions],
        'days': days, 'can_manage': can_manage_fpt_schedule(request.user),
    })


@login_required
@never_cache
@require_POST
@fpt_access(manage=True)
def delete_period(request, period_id):
    with transaction.atomic():
        period = get_object_or_404(FPTPeriod.objects.select_for_update(), pk=period_id)
        period.delete()
    return JsonResponse({'success': True})


@login_required
@never_cache
@require_POST
@fpt_access(manage=True)
def create_session(request):
    data = request_data(request)
    with transaction.atomic():
        session = save_form(FPTSessionForm, data)
        result = session_data(session)
    return JsonResponse({'success': True, 'session': result}, status=201)


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
@fpt_access()
def session_detail(request, session_id):
    if request.method == 'POST':
        data = request_data(request)
        with transaction.atomic():
            session = get_object_or_404(FPTSession.objects.select_for_update(), pk=session_id)
            session = save_form(FPTSessionForm, data, instance=session)
            result = session_data(session)
        return JsonResponse({'success': True, 'session': result})
    session = get_object_or_404(FPTSession.objects.select_related('student', 'instructor'), pk=session_id)
    return JsonResponse({'session': session_data(session)})


@login_required
@never_cache
@require_POST
@fpt_access(manage=True)
def delete_session(request, session_id):
    with transaction.atomic():
        session = get_object_or_404(FPTSession.objects.select_for_update(), pk=session_id)
        session.delete()
    return JsonResponse({'success': True})


@login_required
@never_cache
@require_GET
@fpt_access(manage=True)
def participants(request):
    # No aircraft availability, account balance, or training-phase restrictions.
    users = get_user_model().objects.filter(role__in=['STUDENT', 'INSTRUCTOR']).order_by(
        'first_name', 'last_name', 'username',
    )
    choices = {'students': [], 'instructors': []}
    for user in users:
        choices['students' if user.role == 'STUDENT' else 'instructors'].append({
            'id': user.pk, 'name': participant_name(user, ''),
        })
    return JsonResponse(choices)
