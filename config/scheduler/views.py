from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import timedelta

from .forms import CreateTrainingPeriodForm
from .models import TrainingPeriod, FlightSlot, FlightRequest
from fleet.models import Aircraft

def flight_requests_dashboard(request): 
    """Display the flight requests dashboard."""
    has_active_periods = TrainingPeriod.objects.filter(is_active=True).exists()
    return render(request, 'scheduler/flight_requests_dashboard.html', {
        'has_active_periods': has_active_periods,
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


def create_training_period_grids(request):
    """Generate a grid of slots for created training period."""
    available_periods = TrainingPeriod.objects.filter(is_active=True)
    if not available_periods.exists():
        messages.info(request, 'No hay períodos de entrenamiento activos en este momento.')
        return redirect('scheduler:flight_requests_dashboard')

    # Build grids for each period
    grids = []
    for period in available_periods:
        # Generate dates for this period
        dates = []
        day = period.start_date
        while day <= period.end_date:
            dates.append(day)
            day = day + timedelta(days=1)

        blocks = ['A', 'B', 'C']

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

    context = {
        'grids': grids,
        'user': request.user,
    }
    return render(request, 'scheduler/training_periods.html', context)

@login_required
def create_flight_request(request, slot_id):
    """Create a flight request for a specific slot."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Only students can create flight requests
    if request.user.role != 'STUDENT':
        return JsonResponse({'error': 'Only students can create flight requests'}, status=403)
    
    try:
        slot = get_object_or_404(FlightSlot, id=slot_id)
        
        # Check if slot is free
        if slot.status != 'free':
            return JsonResponse({'error': 'Slot is not available'}, status=400)
        
        # Check if student already has a request for this slot
        existing_request = FlightRequest.objects.filter(
            student=request.user,
            slot=slot
        ).exists()
        
        if existing_request:
            return JsonResponse({'error': 'You already have a request for this slot'}, status=400)
        
        # Create the flight request
        with transaction.atomic():
            flight_request = FlightRequest.objects.create(
                student=request.user,
                slot=slot,
                status='pending'
            )
            # Update slot status to pending
            slot.status = 'pending'
            slot.student = request.user
            slot.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Flight request created successfully',
            'request_id': flight_request.id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def student_scheduler_dashboard(request):
    """Display the student scheduler dashboard."""
    has_active_periods = TrainingPeriod.objects.filter(is_active=True).exists()
    user = request.user
    base_qs = (FlightSlot.objects
               .filter(student=user)
               .select_related('aircraft', 'instructor')
               .order_by('date'))
    approved_slots = base_qs.filter(status='confirmed')[:5]
    pending_slots = base_qs.filter(status='pending')[:5]
    cancelled_slots = base_qs.filter(status='cancelled')[:5]
    return render(request, 'scheduler/student_scheduler_dashboard.html', {
        'has_active_periods': has_active_periods,
        'approved_slots': approved_slots,
        'pending_slots': pending_slots,
        'cancelled_slots': cancelled_slots,
        'user': user,
    })