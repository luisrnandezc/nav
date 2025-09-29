from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from datetime import timedelta
from .forms import CreateFlightPeriodForm
from .models import FlightPeriod, FlightSlot, FlightRequest

def staff_required(view_func):
    """Decorator to check if the user is a staff member."""
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'STAFF':
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper

def role_required(*allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if getattr(request.user, "role", None) not in allowed_roles:
                return JsonResponse({'error': 'Acceso denegado'}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def student_required(view_func):
    """Decorator to check if the user is a student."""
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'STUDENT':
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@staff_required
def flight_requests_dashboard(request): 
    """Display the flight requests dashboard."""
    has_active_periods = FlightPeriod.objects.filter(is_active=True).exists()
    
    # Get flight requests data for all students
    pending_requests = FlightRequest.objects.filter(status='pending').select_related('student', 'slot', 'slot__aircraft', 'slot__instructor').order_by('requested_at')[:20]
    approved_requests = FlightRequest.objects.filter(status='approved').select_related('student', 'slot', 'slot__aircraft', 'slot__instructor').order_by('-requested_at')[:20]
    cancelled_requests = FlightRequest.objects.filter(status='cancelled').select_related('student', 'slot', 'slot__aircraft', 'slot__instructor').order_by('-requested_at')[:20]
    
    return render(request, 'scheduler/flight_requests_dashboard.html', {
        'has_active_periods': has_active_periods,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'cancelled_requests': cancelled_requests,
    })

@login_required
@staff_required
def create_flight_period(request):
    """Create a FlightPeriod and generate slots."""
    if request.method == 'POST':
        form = CreateFlightPeriodForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    period = form.save()
                    created = period.generate_slots()
                messages.success(request, f"Periodo creado. {created} slots generados.")
                form = CreateFlightPeriodForm()  # Reset form with empty data
                return render(request, 'scheduler/create_flight_period.html', {'form': form})
            except (ValidationError, ValueError) as e:
                messages.error(request, f'Error al crear el período: {str(e)}')
                return render(request, 'scheduler/create_flight_period.html', {'form': form})
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
            return render(request, 'scheduler/create_flight_period.html', {'form': form})
    else:
        form = CreateFlightPeriodForm()
    return render(request, 'scheduler/create_flight_period.html', {'form': form})

def create_period_grids(periods):
    """Generate a grid of slots for specified flight periods, grouped by aircraft."""
    # Group periods by aircraft
    aircraft_periods = {}
    for period in periods:
        aircraft = period.aircraft
        if aircraft not in aircraft_periods:
            aircraft_periods[aircraft] = []
        aircraft_periods[aircraft].append(period)
    
    # Build grids for each aircraft
    aircraft_grids = []
    for aircraft, aircraft_period_list in aircraft_periods.items():
        # Sort periods by start_date for this aircraft
        aircraft_period_list.sort(key=lambda p: p.start_date)
        
        aircraft_data = {
            'aircraft': aircraft,
            'periods': []
        }
        
        for period in aircraft_period_list:
            # Generate dates for this period
            dates = []
            day = period.start_date
            while day <= period.end_date:
                dates.append(day)
                day = day + timedelta(days=1)

            blocks = ['AM', 'M', 'PM']

            # Get all slots for this period
            slots = FlightSlot.objects.filter(flight_period=period)
            # Create index by (date, block) since all slots belong to the same aircraft
            slot_index = {(s.date, s.block): s for s in slots}
            
            # Build grid data for this period
            period_data = {
                'period': period,
                'dates': dates,
                'blocks': blocks,
                'grid': {}
            }
            
            for date in dates:
                period_data['grid'][date] = {}
                for block in blocks:
                    slot = slot_index.get((date, block))
                    period_data['grid'][date][block] = slot
            
            aircraft_data['periods'].append(period_data)
        
        aircraft_grids.append(aircraft_data)
    
    return aircraft_grids

@login_required
@student_required
def create_student_flight_period_grids(request):
    """Generate a grid of slots for active flight periods."""
    active_periods = FlightPeriod.objects.filter(is_active=True)
    if not active_periods.exists():
        messages.info(request, 'No hay períodos de vuelo activos en este momento.')
        return redirect('scheduler:flight_requests_dashboard')

    # Filter out advanced aircraft for non-advanced students
    # Advanced aircraft (is_advanced=True) are only visible to advanced students (advanced_student=True)
    try:
        student_profile = request.user.student_profile
        is_advanced_student = student_profile.advanced_student
    except:
        is_advanced_student = False
    
    if not is_advanced_student:
        # Filter out periods for advanced aircraft - non-advanced students can't see them
        active_periods = active_periods.filter(aircraft__is_advanced=False)

    aircraft_grids = create_period_grids(active_periods)

    context = {
        'aircraft_grids': aircraft_grids,
        'user': request.user,
        'is_advanced_student': is_advanced_student,
    }
    return render(request, 'scheduler/student_flight_periods_panel.html', context)

@login_required
@staff_required
def create_staff_flight_period_grids(request):
    """Generate a grid of slots for active and inactive flight periods."""
    periods = FlightPeriod.objects.all()

    aircraft_grids = create_period_grids(periods)

    context = {
        'aircraft_grids': aircraft_grids,
        'user': request.user,
    }
    return render(request, 'scheduler/staff_flight_periods_panel.html', context)

@login_required
@student_required
@require_POST
def create_flight_request(request, slot_id):
    """Create a flight request for a specific slot."""
    slot = get_object_or_404(FlightSlot, id=slot_id)
    try:
        flight_request = FlightRequest()
        flight_request.create_request(request.user, slot)
        return JsonResponse({
            'success': True,
            'message': 'Solicitud de vuelo creada exitosamente',
            'request_id': flight_request.id
        }) 
    except (ValidationError, ValueError) as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Error al crear la solicitud de vuelo: {str(e)}"}, status=500)

@login_required
@staff_required
@require_POST
def approve_flight_request(request, request_id):
    """Approve a flight request and update the slot status to reserved."""
    try:
        flight_request = get_object_or_404(FlightRequest, id=request_id)
        flight_request.approve(flight_request.status)
        
        return JsonResponse({
            'success': True,
            'message': 'Solicitud de vuelo aprobada exitosamente',
            'request_id': flight_request.id,
            'slot_id': flight_request.slot.id
        })
        
    except (ValidationError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@role_required('STAFF', 'STUDENT')
@require_POST
def cancel_flight_request(request, request_id):
    """Cancel a flight request and free up the slot."""
    flight_request = get_object_or_404(FlightRequest, id=request_id)
    
    try:
        flight_request.cancel()
        
        return JsonResponse({
            'success': True,
            'message': 'Solicitud de vuelo cancelada exitosamente',
            'request_id': flight_request.id,
            'slot_id': flight_request.slot.id
        })
        
    except (ValidationError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@staff_required
def change_slot_status(request, slot_id):
    """Change the status of a flight slot (staff only)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try:
        import json
        data = json.loads(request.body)
        action = data.get('action')
        new_status = data.get('new_status')
        
        if not action or not new_status:
            return JsonResponse({'error': 'Acción y nuevo estado requeridos'}, status=400)
        
        slot = get_object_or_404(FlightSlot, id=slot_id)
        with transaction.atomic():
            if action == 'cancel_and_unavailable':
                # First cancel any existing flight request for this slot
                flight_request = FlightRequest.objects.filter(slot=slot).first()
                if flight_request:
                    flight_request.cancel()
                
                # Then set slot to unavailable
                slot.status = 'unavailable'
                slot.student = None
                slot.save()
            elif action in ['available', 'unavailable']:
                # Simply change the slot status
                slot.status = new_status
                if new_status == 'available':
                    slot.student = None  # Clear student if making available
                slot.save()
            else:
                return JsonResponse({'error': 'Acción no válida'}, status=400)
        
        return JsonResponse({
            'success': True,
            'message': f'Estado de la sesión cambiado a {slot.get_status_display()}',
            'slot_id': slot.id,
            'new_status': slot.status
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except (ValidationError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error al cambiar el estado: {str(e)}'}, status=500)

@login_required
@staff_required
def activate_flight_period(request, period_id):
    """Activate a flight period (staff only)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try:
        period = get_object_or_404(FlightPeriod, id=period_id)
        # Check if period is already active
        if period.is_active:
            return JsonResponse({'error': 'Este período ya está activo'}, status=400)
        # Activate the period
        with transaction.atomic():
            period.is_active = True
            period.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Período activado exitosamente para {period.aircraft.registration}',
            'period_id': period.id
        })
    
    except (ValidationError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error al activar el período: {str(e)}'}, status=500)

@login_required
@student_required
def student_scheduler_dashboard(request):
    """Display the student scheduler dashboard."""
    has_active_periods = FlightPeriod.objects.filter(is_active=True).exists()
    user = request.user
    base_qs = (FlightRequest.objects
               .filter(student=user)
               .select_related('slot', 'slot__aircraft', 'slot__instructor')
               .order_by('requested_at'))
    approved_flight_requests = base_qs.filter(status='approved')[:5]
    pending_flight_requests = base_qs.filter(status='pending')[:5]
    cancelled_flight_requests = base_qs.filter(status='cancelled')[:5]
    return render(request, 'scheduler/student_scheduler_dashboard.html', {
        'has_active_periods': has_active_periods,
        'approved_flight_requests': approved_flight_requests,
        'pending_flight_requests': pending_flight_requests,
        'cancelled_flight_requests': cancelled_flight_requests,
        'user': user,
    })