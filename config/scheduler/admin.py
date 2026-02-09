from django.contrib import admin
from .models import FlightPeriod, FlightSlot, FlightRequest, CancellationsFee

# Register your models here.

@admin.register(FlightPeriod)
class FlightPeriodAdmin(admin.ModelAdmin):
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
    list_display = ('flight_period', 'date', 'block', 'aircraft', 'instructor', 'student', 'status')
    list_filter = ('date', 'block', 'status', 'aircraft', 'instructor')
    search_fields = ('aircraft__registration', 'instructor__first_name', 'instructor__last_name', 'student__first_name', 'student__last_name')
    list_editable = ('status',)
    date_hierarchy = 'date'
    ordering = ('date', 'block', 'aircraft')
    
    fieldsets = (
        ('Información básica', {
            'fields': ('flight_period', 'date', 'block', 'status')
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
    list_display = ('student', 'slot', 'status', 'requested_at')
    list_filter = ('status', 'requested_at', 'slot__date', 'slot__block')
    search_fields = ('student__first_name', 'student__last_name', 'slot__aircraft__registration', 'notes')
    date_hierarchy = 'requested_at'
    ordering = ('-requested_at',)
    readonly_fields = ('requested_at', 'updated_at')
    actions = ['approve_requests', 'cancel_requests']
    
    fieldsets = (
        ('Información básica', {
            'fields': ('student', 'slot', 'status')
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
    
    def delete_model(self, request, obj):
        """Override delete to use custom delete method."""
        obj.delete()
    
    def delete_queryset(self, request, queryset):
        """Override bulk delete to use custom delete method for each object."""
        for obj in queryset:
            obj.delete()
    
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

@admin.register(CancellationsFee)
class CancellationsFeeAdmin(admin.ModelAdmin):
    list_display = ('flight_request_id_display', 'student_display', 'amount', 'flight_date_display', 'date_added')
    list_filter = ('date_added', 'amount', 'flight_request__slot__date')
    search_fields = ('cancelled_by_name', 'flight_request__student__username', 'flight_request__slot__aircraft__registration')
    date_hierarchy = 'date_added'
    ordering = ('-date_added',)
    readonly_fields = ('flight_request', 'cancelled_by_name', 'amount', 'date_added')
    actions = ['reimburse_selected_fees']
    
    # Prevent adding/editing since fees are created programmatically
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    fieldsets = (
        ('Información de la multa', {
            'fields': ('flight_request', 'cancelled_by_name', 'amount', 'date_added')
        }),
    )
    
    def flight_request_id_display(self, obj):
        """Display just the flight request ID."""
        if obj.flight_request:
            return f"#{obj.flight_request.id}"
        return "N/A"
    flight_request_id_display.short_description = "ID Solicitud"
    flight_request_id_display.admin_order_field = 'flight_request__id'
    
    def student_display(self, obj):
        """Display student name (from request or stored cancelled_by_name)."""
        if obj.flight_request and obj.flight_request.student:
            student = obj.flight_request.student
            return f"{student.first_name} {student.last_name} ({student.username})"
        if obj.cancelled_by_name:
            return obj.cancelled_by_name
        return "N/A"
    student_display.short_description = "Estudiante"
    
    def flight_date_display(self, obj):
        """Display the original flight date."""
        if obj.flight_request and obj.flight_request.slot:
            return obj.flight_request.slot.date.strftime('%d/%m/%Y')
        return "N/A"
    flight_date_display.short_description = "Fecha del vuelo"
    
    def reimburse_selected_fees(self, request, queryset):
        """Reimburse selected fees."""
        reimbursed_count = 0
        for fee in queryset:
            try:
                fee.delete()
                reimbursed_count += 1
                
            except Exception as e:
                self.message_user(request, f"Error reembolsando multa {fee.id}: {str(e)}", level='ERROR')
        
        if reimbursed_count > 0:
            self.message_user(request, f"{reimbursed_count} multa(s) reembolsada(s) exitosamente.")
    
    reimburse_selected_fees.short_description = "Reembolsar multas seleccionadas"
    
    def delete_model(self, request, obj):
        """Override delete to use custom delete method."""
        obj.delete()
        self.message_user(request, f"Multa de ${obj.amount} reembolsada a {obj.student_display()}")
    
    def delete_queryset(self, request, queryset):
        """Override bulk delete to use custom delete method for each object."""
        for obj in queryset:
            obj.delete()
