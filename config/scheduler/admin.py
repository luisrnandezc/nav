from django.contrib import admin
from .models import TrainingPeriod, FlightSlot, FlightRequest

# Register your models here.

@admin.register(TrainingPeriod)
class TrainingPeriodAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'start_date', 'end_date', 'aircraft', 'is_active', 'created_at')
    list_filter = ('is_active', 'aircraft', 'start_date', 'end_date', 'created_at')
    search_fields = ('start_date', 'end_date', 'aircraft__registration')
    list_editable = ('is_active',)
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información del período', {
            'fields': ('__str__', 'start_date', 'end_date', 'aircraft', 'is_active')
        }),
        ('Fechas del sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(FlightSlot)
class FlightSlotAdmin(admin.ModelAdmin):
    list_display = ('training_period', 'date', 'block', 'aircraft', 'instructor', 'student', 'status')
    list_filter = ('date', 'block', 'status', 'aircraft', 'instructor')
    search_fields = ('aircraft__registration', 'instructor__first_name', 'instructor__last_name', 'student__first_name', 'student__last_name')
    list_editable = ('status',)
    date_hierarchy = 'date'
    ordering = ('date', 'block', 'aircraft')
    
    fieldsets = (
        ('Información básica', {
            'fields': ('training_period', 'date', 'block', 'status')
        }),
        ('Personal', {
            'fields': ('instructor', 'student')
        }),
        ('Aeronave', {
            'fields': ('aircraft',)
        }),
    )

@admin.register(FlightRequest)
class FlightRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'slot', 'status', 'flexible', 'requested_at')
    list_filter = ('status', 'flexible', 'requested_at', 'slot__date', 'slot__block')
    search_fields = ('student__first_name', 'student__last_name', 'slot__aircraft__registration', 'notes')
    list_editable = ('status',)
    date_hierarchy = 'requested_at'
    ordering = ('-requested_at',)
    readonly_fields = ('requested_at', 'updated_at')
    
    fieldsets = (
        ('Información básica', {
            'fields': ('student', 'slot', 'status')
        }),
        ('Opciones', {
            'fields': ('flexible',)
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
        ('Fechas', {
            'fields': ('requested_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
