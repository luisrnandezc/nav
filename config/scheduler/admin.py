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
            'fields': ('start_date', 'end_date', 'aircraft', 'is_active')
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
    date_hierarchy = 'requested_at'
    ordering = ('-requested_at',)
    readonly_fields = ('requested_at', 'updated_at')
    actions = ['approve_requests', 'cancel_requests']
    
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
    
    def approve_requests(self, request, queryset):
        """Approve selected flight requests."""
        approved_count = 0
        for flight_request in queryset.filter(status='pending'):
            try:
                flight_request.approve()
                approved_count += 1
            except ValueError as e:
                self.message_user(request, f"Error aprobando solicitud {flight_request.id}: {str(e)}", level='ERROR')
        
        if approved_count > 0:
            self.message_user(request, f"{approved_count} solicitud(es) de vuelo aprobadas exitosamente.")
    
    approve_requests.short_description = "Aprobar solicitudes de vuelo seleccionadas"
    
    def cancel_requests(self, request, queryset):
        """Cancel selected flight requests."""
        cancelled_count = 0
        for flight_request in queryset.filter(status__in=['pending', 'approved']):
            try:
                flight_request.cancel()
                cancelled_count += 1
            except ValueError as e:
                self.message_user(request, f"Error cancelando solicitud {flight_request.id}: {str(e)}", level='ERROR')
        
        if cancelled_count > 0:
            self.message_user(request, f"{cancelled_count} solicitud(es) de vuelo canceladas exitosamente.")
    
    cancel_requests.short_description = "Cancelar solicitudes de vuelo seleccionadas"
    
    def save_model(self, request, obj, form, change):
        """Override save to use custom approve/cancel methods when status changes."""
        if change:  # Only for existing objects
            # Get the original object from database BEFORE any changes
            original = FlightRequest.objects.get(pk=obj.pk)
            original_status = original.status
            # Check if status changed
            if original_status != obj.status:
                if obj.status == 'approved' and original_status == 'pending':
                    # Use our custom approve method with original status
                    obj.approve(original_status=original_status)
                    return
                elif obj.status == 'cancelled' and original_status in ['pending', 'approved']:
                    # Use our custom cancel method
                    obj.cancel()
                    return
        
        # For new objects or no status change, use normal save
        super().save_model(request, obj, form, change)
