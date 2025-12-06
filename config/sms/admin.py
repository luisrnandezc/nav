from django.contrib import admin
from .models import VoluntaryHazardReport, Risk, MitigationAction


@admin.register(VoluntaryHazardReport)
class VoluntaryHazardReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'date', 'time', 'area', 'is_resolved', 'ai_analysis_status', 'is_valid', 'created_at')
    list_filter = ('ai_analysis_status', 'area', 'is_resolved', 'date', 'is_valid')
    search_fields = ('description', 'first_name', 'last_name', 'area', 'code', 'is_resolved')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Información del Reporte', {
            'fields': ('code', 'date', 'time', 'area', 'description', 'is_valid', 'invalidity_reason', 'mmrs_created', 'is_resolved')
        }),
        ('Información del Reportante', {
            'fields': ('is_anonymous', 'first_name', 'last_name', 'role')
        }),
        ('Análisis de IA', {
            'fields': ('ai_analysis_status', 'ai_analysis_result', 'analysis_email_sent')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = ('id', 'report', 'pre_evaluation', 'status', 'condition', 'created_at')
    list_filter = ('report__code', 'status', 'condition', 'created_at')
    search_fields = ('description', 'report__description', 'report__code')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Información del Riesgo', {
            'fields': ('report', 'description', 'status', 'condition')
        }),
        ('Evaluación pre-mitigación', {
            'fields': ('pre_evaluation_severity', 'pre_evaluation_probability')
        }),
        ('Evaluación post-mitigación', {
            'fields': ('post_evaluation_severity', 'post_evaluation_probability')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MitigationAction)
class MitigationActionAdmin(admin.ModelAdmin):
    list_display = ('id', 'risk', 'status', 'due_date', 'created_at')
    list_filter = ('status', 'due_date', 'created_at')
    search_fields = ('description', 'risk__description', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Información de la Acción', {
            'fields': ('risk', 'description')
        }),
        ('Estado y Fechas', {
            'fields': ('status', 'due_date')
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

