from django.contrib import admin
from .models import VoluntaryReport, ReportAnalysis
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
    
    def description_preview(self, obj):
        """Show a preview of the description in the list view"""
        if obj.description:
            return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
        return "Sin descripción"
    description_preview.short_description = "Descripción"

@admin.register(ReportAnalysis)
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
        'report', 'created_at'
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
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def created_at(self, obj):
        """Show when the analysis was created"""
        return datetime.now()
    created_at.short_description = "Fecha de análisis"