from django.contrib import admin
from .models import VoluntaryReport, ReportAnalysis, SMSAction
from datetime import datetime

@admin.register(VoluntaryReport)
class VoluntaryReportAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'area', 'ai_analysis_status', 'description_preview'
    ]
    list_filter = [
        'area', 'ai_analysis_status'
    ]
    search_fields = [
        'date', 'area', 'description'
    ]
    ordering = ['-id']
    
    fieldsets = (
        ('1. Datos del reporte', {
            'fields': ('first_name', 'last_name', 'role', 'date', 'time')
        }),
        ('2. Área del peligro', {
            'fields': ('area',)
        }),
        ('3. Descripción del peligro', {
            'fields': ('description',)
        }),
        ('4. Estado del análisis de IA', {
            'fields': ('ai_analysis_status',)
        }),
        ('5. Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'ai_analysis_status']
    
    def has_add_permission(self, request):
        """Disable adding new reports through admin - reports must be created through the website"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing reports through admin - reports must be managed through the website"""
        return False
    
    def description_preview(self, obj):
        """Show a preview of the description in the list view"""
        if obj.description:
            return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
        return "Sin descripción"
    description_preview.short_description = "Descripción"

@admin.register(ReportAnalysis)
class ReportAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        'report', 'is_valid', 'severity', 'probability', 'actions_created', 'created_at'
    ]
    list_filter = [
        'is_valid', 'severity', 'probability', 'actions_created'
    ]
    search_fields = [
        'report__date', 'report__area', 'risk_analysis', 'recommendations'
    ]
    readonly_fields = [
        'report', 'created_at'
    ]
    ordering = ['-id']
    
    fieldsets = (
        ('Información del reporte', {
            'fields': ('report',)
        }),
        ('Resultados de análisis', {
            'fields': ('is_valid', 'severity', 'probability', 'value', 'actions_created')
        }),
        ('Análisis detallado', {
            'fields': ('risk_analysis', 'recommendations')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def created_at(self, obj):
        """Show when the analysis was created"""
        return datetime.now()
    created_at.short_description = "Fecha de análisis"

@admin.register(SMSAction)
class SMSActionAdmin(admin.ModelAdmin):
    list_display = [
        'report', 'status', 'assigned_to_username', 'due_date', 'is_overdue_display', 'created_at'
    ]
    list_filter = [
        'status', 'assigned_to', 'due_date', 'created_at'
    ]
    search_fields = [
        'description', 'report__report__date', 'report__report__area', 'assigned_to__username'
    ]
    readonly_fields = [
        'created_at'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Información del reporte', {
            'fields': ('report',)
        }),
        ('Detalles de la acción', {
            'fields': ('description', 'status', 'assigned_to', 'due_date')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def assigned_to_username(self, obj):
        """Show only the username of the assigned user"""
        return obj.assigned_to.username if obj.assigned_to else "Sin asignar"
    assigned_to_username.short_description = "Asignado a"
    assigned_to_username.admin_order_field = 'assigned_to__username'
    
    def is_overdue_display(self, obj):
        """Show if the action is overdue"""
        if obj.is_overdue():
            return "⚠️ VENCIDA"
        return "✅ Al día"
    is_overdue_display.short_description = "Estatus de vencimiento"
    is_overdue_display.admin_order_field = 'due_date'
    
    def get_queryset(self, request):
        """Optimize queries by selecting related objects"""
        return super().get_queryset(request).select_related('report__report', 'assigned_to')