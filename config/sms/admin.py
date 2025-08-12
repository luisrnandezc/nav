from django.contrib import admin
from .models import voluntary_report

@admin.register(voluntary_report)
class VoluntaryReportAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'area', 'ai_analysis_preview'
    ]
    list_filter = [
        'area'
    ]
    search_fields = [
        'date', 'area'
    ]
    ordering = ['-id']
    
    # Make ai_analysis field read-only so users can't edit it manually
    readonly_fields = [
        'ai_analysis'
    ]
    
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
        ('4. Condición del reporte', {
            'fields': ('report_condition', 'invalid_reason')
        }),
        ('5. Recibido por', {
            'fields': ('coordinator_first_name', 'coordinator_last_name', 'coordinator_id',
                        'report_code', 'received_date')
        }),
        ('6. Análisis AI', {
            'fields': ('ai_analysis',),
            'description': 'Análisis generado automáticamente por AI (no editable manualmente)'
        })
    )
    
    def ai_analysis_preview(self, obj):
        """Show a preview of the AI analysis in the list view"""
        if obj.ai_analysis:
            return obj.ai_analysis[:50] + "..." if len(obj.ai_analysis) > 50 else obj.ai_analysis
        return "No hay análisis"
    ai_analysis_preview.short_description = "Análisis AI"
