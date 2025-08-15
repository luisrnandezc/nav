from django.contrib import admin
from .models import voluntary_report, report_analysis
from datetime import datetime

@admin.register(voluntary_report)
class VoluntaryReportAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'area', 'description_preview'
    ]
    list_filter = [
        'area'
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
    )
    
    def description_preview(self, obj):
        """Show a preview of the description in the list view"""
        if obj.description:
            return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
        return "Sin descripción"
    description_preview.short_description = "Descripción"

@admin.register(report_analysis)
class ReportAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        'report', 'is_valid', 'severity', 'probability', 'created_at'
    ]
    list_filter = [
        'is_valid', 'severity', 'probability'
    ]
    search_fields = [
        'report__date', 'report__area', 'risk_analysis', 'recommendations'
    ]
    readonly_fields = [
        'report'
    ]
    ordering = ['-id']
    
    fieldsets = (
        ('Información del reporte', {
            'fields': ('report',)
        }),
        ('Resultados de análisis', {
            'fields': ('is_valid', 'severity', 'probability', 'value')
        }),
        ('Análisis detallado', {
            'fields': ('risk_analysis', 'recommendations')
        }),
    )
    
    def created_at(self, obj):
        """Show when the analysis was created"""
        return datetime.now()
    created_at.short_description = "Fecha de análisis"