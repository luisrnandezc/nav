from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .forms import TrainingPeriodForm
from .models import TrainingPeriod, FlightSlot
from fleet.models import Aircraft

def flight_requests_dashboard(request): 
    """Display the flight requests dashboard."""
    return render(request, 'scheduler/flight_requests_dashboard.html')

def create_training_period(request):
    """Create a TrainingPeriod and generate slots."""
    if request.method == 'POST':
        form = TrainingPeriodForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                period = form.save()
                created = period.generate_slots()
            messages.success(request, f"Periodo creado. {created} slots generados.")
            return redirect(reverse('scheduler:training_period_calendar', args=[period.id]))
    else:
        form = TrainingPeriodForm()
    return render(request, 'scheduler/training_period_form.html', {'form': form})


def training_period_calendar(request, pk):
    """Display a grid calendar per aircraft for a training period."""
    period = get_object_or_404(TrainingPeriod, pk=pk)
    aircraft_list = Aircraft.objects.filter(is_active=True)

    # Build a simple in-memory structure: {aircraft: {date: {block: slot}}}
    dates = []
    day = period.start_date
    while day <= period.end_date:
        dates.append(day)
        day = day + timedelta(days=1)

    blocks = ['A', 'B', 'C']

    grid = {}
    slots = FlightSlot.objects.filter(training_period=period).select_related('aircraft')
    # index by (aircraft_id, date, block)
    index = {(s.aircraft_id, s.date, s.block): s for s in slots}
    for aircraft in aircraft_list:
        per_aircraft = {}
        for date in dates:
            per_aircraft[date] = {block: index.get((aircraft.id, date, block)) for block in blocks}
        grid[aircraft] = per_aircraft

    context = {
        'period': period,
        'dates': dates,
        'blocks': blocks,
        'grid': grid,
    }
    return render(request, 'scheduler/calendar.html', context)


# Create your views here.
