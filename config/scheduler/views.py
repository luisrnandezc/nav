from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import timedelta
from .forms import CreateTrainingPeriodForm
from .models import TrainingPeriod, FlightSlot, FlightRequest

def flight_requests_dashboard(request): 
    """Display the flight requests dashboard."""
    has_active_periods = TrainingPeriod.objects.filter(is_active=True).exists()
    
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

def check_training_period_overlap(period):
    """Check if there is a training period overlap for the same aircraft."""
    existing_periods = TrainingPeriod.objects.filter(aircraft=period.aircraft)
    if existing_periods.exists():
        for existing_period in existing_periods:
            # Two periods overlap if: start1 < end2 AND start2 < end1
            if period.start_date <= existing_period.end_date and existing_period.start_date <= period.end_date:
                return True
        return False
    return False

def create_training_period(request):
    """Create a TrainingPeriod and generate slots."""
    if request.method == 'POST':
        form = CreateTrainingPeriodForm(request.POST)
        if form.is_valid():
            if check_training_period_overlap(form.instance):
                form.add_error('end_date', 'Ya existe un período de entrenamiento en el rango de fechas seleccionado.')
                return render(request, 'scheduler/create_training_period.html', {'form': form})
            with transaction.atomic():
                period = form.save()
                created = period.generate_slots()
            messages.success(request, f"Periodo creado. {created} slots generados.")
            form = CreateTrainingPeriodForm()  # Reset form with empty data
            return render(request, 'scheduler/create_training_period.html', {'form': form})
    else:
        form = CreateTrainingPeriodForm()
    return render(request, 'scheduler/create_training_period.html', {'form': form})

def create_period_grids(periods):
    """Generate a grid of slots for specified training periods."""
    # Build grids for each period
    grids = []
    for period in periods:
        # Generate dates for this period
        dates = []
        day = period.start_date
        while day <= period.end_date:
            dates.append(day)
            day = day + timedelta(days=1)

        blocks = ['AM', 'M', 'PM']

        # Get all slots for this period (only for the period's aircraft)
        slots = FlightSlot.objects.filter(training_period=period)
        # Create index by (date, block) since all slots belong to the same aircraft
        slot_index = {(s.date, s.block): s for s in slots}
        
        # Build grid data for this period
        period_data = {
            'period': period,
            'dates': dates,
            'blocks': blocks,
            'aircraft_grids': []
        }
        
        # Create grid only for the period's aircraft
        aircraft_data = {
            'aircraft': period.aircraft,
            'grid': {}
        }
        
        for date in dates:
            aircraft_data['grid'][date] = {}
            for block in blocks:
                slot = slot_index.get((date, block))
                aircraft_data['grid'][date][block] = slot
        
        period_data['aircraft_grids'].append(aircraft_data)
        grids.append(period_data)
    return grids

@login_required
def create_student_training_period_grids(request):
    """Generate a grid of slots for active training periods."""
    active_periods = TrainingPeriod.objects.filter(is_active=True)
    if not active_periods.exists():
        messages.info(request, 'No hay períodos de entrenamiento activos en este momento.')
        return redirect('scheduler:flight_requests_dashboard')

    grids = create_period_grids(active_periods)

    context = {
        'grids': grids,
        'user': request.user,
    }
    return render(request, 'scheduler/student_periods_panel.html', context)

@login_required
def create_staff_training_period_grids(request):
    """Generate a grid of slots for active and inactive training periods."""
    periods = TrainingPeriod.objects.all()

    grids = create_period_grids(periods)

    context = {
        'grids': grids,
        'user': request.user,
    }
    return render(request, 'scheduler/staff_periods_panel.html', context)

@login_required
def create_flight_request(request, slot_id):
    """Create a flight request for a specific slot."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Only students can create flight requests
    if request.user.role != 'STUDENT':
        return JsonResponse({'error': 'Solo estudiantes pueden crear solicitudes de vuelo'}, status=403)
    
    try:
        slot = get_object_or_404(FlightSlot, id=slot_id)
        
        # Check if slot is available
        if slot.status != 'available':
            return JsonResponse({'error': 'La sesión no está disponible'}, status=400)
        
        # Check if student already has a request for this slot
        existing_request = FlightRequest.objects.filter(
            student=request.user,
            slot=slot,
            status__in=['pending', 'approved']
        ).exists()
        
        if existing_request:
            return JsonResponse({'error': 'Ya tiene una solicitud de vuelo para esta sesión'}, status=400)
        
        # Check student balance (safety net)
        try:
            student_profile = request.user.student_profile
            balance = student_profile.balance
            if balance < 500:
                return JsonResponse({
                    'error': f'Balance insuficiente. Su balance actual es ${balance}. Se requiere un mínimo de $500 para solicitar vuelos.'
                }, status=400)
        except Exception:
            return JsonResponse({'error': 'No se pudo verificar el balance del estudiante'}, status=400)
        
        # Check student approved or pending requests
        max_requests = balance // 500
        existing_requests = FlightRequest.objects.filter(
            student=request.user,
            status__in=['pending', 'approved']
        )
        if existing_requests.exists() and existing_requests.count() >= max_requests:
            return JsonResponse({'error': f'Ya tiene el máximo de {max_requests} solicitudes de vuelo aprobadas o pendientes'}, status=400)
        
        # Create the flight request
        with transaction.atomic():
            flight_request = FlightRequest.objects.create(
                student=request.user,
                slot=slot,
                status='pending'
            )
            # Update slot status to unavailable
            slot.status = 'unavailable'
            slot.student = request.user
            slot.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Solicitud de vuelo creada exitosamente',
            'request_id': flight_request.id
        })
        
    except Exception:
        return JsonResponse({'error': 'Error al crear la solicitud de vuelo'}, status=500)

@login_required
def approve_flight_request(request, request_id):
    """Approve a flight request and update the slot status to reserved."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Only staff can approve flight requests
    if request.user.role != 'STAFF':
        return JsonResponse({'error': 'Solo el staff puede aprobar solicitudes de vuelo'}, status=403)
    
    try:
        flight_request = get_object_or_404(FlightRequest, id=request_id)
        
        # Check if request is pending
        if flight_request.status != 'pending':
            return JsonResponse({'error': 'Solo solicitudes pendientes pueden ser aprobadas'}, status=400)
        
        # Approve the request (this will also update the slot status)
        flight_request.approve()
        
        return JsonResponse({
            'success': True,
            'message': 'Solicitud de vuelo aprobada exitosamente',
            'request_id': flight_request.id,
            'slot_id': flight_request.slot.id
        })
        
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def cancel_flight_request(request, request_id):
    """Cancel a flight request and free up the slot."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Only staff or the student who made the request can cancel
    flight_request = get_object_or_404(FlightRequest, id=request_id)
    if request.user.role != 'STAFF' and request.user != flight_request.student:
        return JsonResponse({'error': 'Solo el staff o el estudiante puede cancelar sus propias solicitudes'}, status=403)
    
    try:
        # Check if request can be cancelled
        if flight_request.status not in ['pending', 'approved']:
            return JsonResponse({'error': 'Solo solicitudes pendientes o aprobadas pueden ser canceladas'}, status=400)
        
        # Cancel the request (this will also free up the slot)
        flight_request.cancel()
        
        return JsonResponse({
            'success': True,
            'message': 'Solicitud de vuelo cancelada exitosamente',
            'request_id': flight_request.id,
            'slot_id': flight_request.slot.id
        })
        
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def change_slot_status(request, slot_id):
    """Change the status of a flight slot (staff only)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Only staff can change slot status
    if request.user.role != 'STAFF':
        return JsonResponse({'error': 'Solo el staff puede cambiar el estado de las sesiones'}, status=403)
    
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
    except Exception as e:
        return JsonResponse({'error': f'Error al cambiar el estado: {str(e)}'}, status=500)

@login_required
def activate_training_period(request, period_id):
    """Activate a training period (staff only)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Only staff can activate periods
    if request.user.role != 'STAFF':
        return JsonResponse({'error': 'Solo el staff puede activar períodos de entrenamiento'}, status=403)
    
    try:
        period = get_object_or_404(TrainingPeriod, id=period_id)
        
        # Check if period is already active
        if period.is_active:
            return JsonResponse({'error': 'Este período ya está activo'}, status=400)
        
        # Check if there's already an active period for this aircraft
        existing_active_period = TrainingPeriod.objects.filter(
            aircraft=period.aircraft,
            is_active=True
        ).exclude(id=period.id).first()
        
        if existing_active_period:
            return JsonResponse({
                'error': f'Ya existe un período activo para la aeronave {period.aircraft.registration}. ' +
                        f'Debe desactivar el período actual ({existing_active_period.start_date} - {existing_active_period.end_date}) ' +
                        'antes de activar este período.'
            }, status=400)
        
        # Activate the period
        with transaction.atomic():
            period.is_active = True
            period.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Período activado exitosamente para {period.aircraft.registration}',
            'period_id': period.id
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error al activar el período: {str(e)}'}, status=500)

def student_scheduler_dashboard(request):
    """Display the student scheduler dashboard."""
    has_active_periods = TrainingPeriod.objects.filter(is_active=True).exists()
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