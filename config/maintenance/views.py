from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from fleet.models import Aircraft
from fms.models import DiscrepancyReport


CURRENT_STATUSES = ('PENDING', 'IN_PROGRESS')


@login_required
def discrepancy_reports_panel(request):
    """Display current aircraft discrepancy reports for authorized staff."""
    if request.user.role != 'STAFF':
        messages.error(request, 'Acceso no autorizado')
        return redirect('dashboard:dashboard')

    if not request.user.has_perm('fms.view_discrepancyreport'):
        messages.error(request, 'No tiene permisos para ver reportes de discrepancia.')
        return redirect('dashboard:dashboard')

    status_filter = request.GET.get('status', 'current')
    type_filter = request.GET.get('type', '').strip()
    aircraft_filter = request.GET.get('aircraft', '').strip()

    reports = DiscrepancyReport.objects.select_related('aircraft').order_by('-created_at')

    if status_filter == 'current':
        reports = reports.filter(status__in=CURRENT_STATUSES)
    elif status_filter:
        reports = reports.filter(status=status_filter)

    if type_filter:
        reports = reports.filter(discrepancy_type=type_filter)

    if aircraft_filter:
        reports = reports.filter(aircraft_id=aircraft_filter)

    all_reports = DiscrepancyReport.objects.all()
    context = {
        'reports': reports,
        'aircraft_list': Aircraft.objects.filter(is_active=True).order_by('registration'),
        'status_choices': DiscrepancyReport.STATUS_CHOICES,
        'type_choices': DiscrepancyReport.TYPE_CHOICES,
        'selected_status': status_filter,
        'selected_type': type_filter,
        'selected_aircraft': aircraft_filter,
        'current_count': all_reports.filter(status__in=CURRENT_STATUSES).count(),
        'pending_count': all_reports.filter(status='PENDING').count(),
        'in_progress_count': all_reports.filter(status='IN_PROGRESS').count(),
        'completed_count': all_reports.filter(status='COMPLETED').count(),
    }
    return render(request, 'maintenance/discrepancy_reports_panel.html', context)
