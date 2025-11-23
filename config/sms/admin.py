from django.contrib import admin
from .models import VoluntaryHazardReport


@admin.register(VoluntaryHazardReport)
class VoluntaryHazardReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'time', 'area', 'is_anonymous', 'ai_analysis_status', 'created_at')
    list_filter = ('ai_analysis_status', 'area', 'is_anonymous', 'date')
    search_fields = ('description', 'first_name', 'last_name', 'area')
    readonly_fields = ('created_at', 'updated_at', 'ai_analysis_result')
    fieldsets = (
        ('Información del Reporte', {
            'fields': ('date', 'time', 'area', 'description')
        }),
        ('Información del Reportante', {
            'fields': ('is_anonymous', 'first_name', 'last_name', 'role')
        }),
        ('Análisis de IA', {
            'fields': ('ai_analysis_status', 'ai_analysis_result')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

