from django.contrib import admin
from .models import Simulator, Aircraft, AircraftAvailability, AircraftHours

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
