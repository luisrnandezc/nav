from django.contrib import admin
from django.contrib import messages
from django.db.models import Sum
from .models import Simulator, Aircraft, AircraftAvailability, AircraftHours
from fms.models import FlightEvaluation0_100, FlightEvaluation100_120, FlightEvaluation120_170, FlightReport

def recompute_aircraft_total_hours(modeladmin, request, queryset):
    """
    Custom admin action to recompute aircraft total flight hours
    by summing all session_flight_hours from flight evaluation models and flight reports
    """
    updated_count = 0
    
    for aircraft in queryset:
        # Sum session_flight_hours from all flight evaluation models
        total_0_100 = FlightEvaluation0_100.objects.filter(aircraft=aircraft).aggregate(
            total=Sum('session_flight_hours')
        )['total'] or 0
        
        total_100_120 = FlightEvaluation100_120.objects.filter(aircraft=aircraft).aggregate(
            total=Sum('session_flight_hours')
        )['total'] or 0
        
        total_120_170 = FlightEvaluation120_170.objects.filter(aircraft=aircraft).aggregate(
            total=Sum('session_flight_hours')
        )['total'] or 0
        
        # Sum flight_hours from flight reports
        total_flight_reports = FlightReport.objects.filter(aircraft=aircraft).aggregate(
            total=Sum('flight_hours')
        )['total'] or 0
        
        # Calculate total hours
        total_hours = total_0_100 + total_100_120 + total_120_170 + total_flight_reports
        
        # Update aircraft total_hours
        aircraft.total_hours = total_hours
        aircraft.save()
        updated_count += 1
    
    # Show success message
    if updated_count == 1:
        messages.success(request, f'Successfully recomputed total hours for 1 aircraft.')
    else:
        messages.success(request, f'Successfully recomputed total hours for {updated_count} aircraft.')

recompute_aircraft_total_hours.short_description = "Actualizar horas totales de las aeronaves seleccionadas"

@admin.register(Simulator)
class SimulatorAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'is_available', 'hourly_rate_single', 'hourly_rate_dual', 'total_hours']
    list_filter = ['is_active', 'is_available']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Información básica', {
            'fields': ('name', 'is_active', 'is_available', 'hourly_rate_single', 'hourly_rate_dual')
        }),
        ('Registro de horas', {
            'fields': ('total_hours',)
        }),
        ('Misceláneos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = ['registration', 'manufacturer', 'model', 'is_active', 'is_available', 'maintenance_status', 'total_hours']
    list_filter = ['is_active', 'is_available', 'maintenance_status']
    search_fields = ['registration', 'model', 'serial_number']
    readonly_fields = ['created_at', 'updated_at']
    actions = [recompute_aircraft_total_hours]
    fieldsets = (
        ('Basic Information', {
            'fields': ('manufacturer', 'model', 'registration', 'serial_number', 'year_manufactured')
        }),
        ('Operational Status', {
            'fields': ('is_active', 'is_available', 'maintenance_status', 'total_hours')
        }),
        ('Scheduling Configuration', {
            'fields': ('max_daily_slots', 'hourly_rate', 'fuel_cost', 'is_advanced')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AircraftAvailability)
class AircraftAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['aircraft', 'date', 'is_available', 'reason']
    list_filter = ['is_available', 'date', 'aircraft']
    search_fields = ['aircraft__registration', 'reason']
    date_hierarchy = 'date'
    ordering = ['-date', 'aircraft']

@admin.register(AircraftHours)
class AircraftHoursAdmin(admin.ModelAdmin):
    list_display = ['aircraft', 'date', 'hours_flown', 'total_hours', 'recorded_by']
    list_filter = ['date', 'aircraft', 'recorded_by']
    search_fields = ['aircraft__registration', 'recorded_by__username', 'notes']
    date_hierarchy = 'date'
    ordering = ['-date', 'aircraft']
    readonly_fields = ['total_hours']
