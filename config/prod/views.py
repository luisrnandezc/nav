from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from accounts.models import StudentProfile

from .forms import ProductionFilterForm
from .services import ProductionFilters, get_production_report


@login_required
@permission_required('accounts.can_view_production', raise_exception=True)
def production_panel(request):
    """Display the filters and production report on a single protected page."""
    today = date.today()
    initial = {
        'start_date': today - timedelta(days=30),
        'end_date': today,
    }
    form = ProductionFilterForm(request.GET or None, initial=initial)
    report = None
    chart_data = None
    student_balances, total_student_balance = _student_balance_status()

    if request.GET and form.is_valid():
        report = get_production_report(
            ProductionFilters(
                start_date=form.cleaned_data['start_date'],
                end_date=form.cleaned_data['end_date'],
                aircraft_registrations=_one_value_tuple(
                    form.cleaned_data['aircraft'],
                    'registration',
                ),
                simulator_ids=_one_value_tuple(
                    form.cleaned_data['simulators'],
                    'pk',
                ),
                instructor_ids=_profile_id_tuple(
                    form.cleaned_data['instructors'],
                ),
                student_ids=_profile_id_tuple(form.cleaned_data['students']),
            )
        )
        chart_data = _flight_chart_data(report)

    return render(
        request,
        'prod/production_panel.html',
        {
            'form': form,
            'report': report,
            'chart_data': chart_data,
            'student_balances': student_balances,
            'total_student_balance': total_student_balance,
            'total_balance_badge': (
                'badge-green' if total_student_balance >= 0 else 'badge-red'
            ),
        },
    )


def _one_value_tuple(selected_object, attribute):
    """Convert one optional form selection to the tuple expected by the service."""
    if selected_object is None:
        return ()
    return (getattr(selected_object, attribute),)


def _profile_id_tuple(profile):
    """Convert one optional student or instructor profile to a national-ID tuple."""
    if profile is None:
        return ()
    return (profile.user.national_id,)


def _student_balance_status():
    """Return current balances for every FLYING student and their total."""

    profiles = StudentProfile.objects.filter(
        student_phase=StudentProfile.FLYING,
    ).select_related('user').order_by('user__first_name', 'user__last_name')
    rows = []
    total = Decimal('0.00')

    for profile in profiles:
        balance = profile.balance or Decimal('0.00')
        total += balance
        if balance >= Decimal('500.00'):
            badge = 'badge-green'
        elif balance >= 0:
            badge = 'badge-yellow'
        else:
            badge = 'badge-red'
        rows.append({
            'name': profile.user.get_full_name() or profile.user.username,
            'national_id': profile.user.national_id,
            'balance': balance,
            'badge': badge,
        })

    return rows, total


def _flight_chart_data(report):
    """Convert decimal trend totals into browser-ready chart datasets."""

    trend = report.flight_trend
    return {
        'labels': trend.labels,
        'grouping': trend.grouping,
        'flight_hours': [float(value) for value in trend.flight_hours],
        'income_usd': [float(value) for value in trend.income_usd],
        'operating_income_usd': [
            float(value) for value in trend.operating_income_usd
        ],
        'aircraft_hours': {
            registration: [float(value) for value in values]
            for registration, values in trend.aircraft_hours.items()
        },
    }
