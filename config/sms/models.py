from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json

class VoluntaryReport(models.Model):
    """
    Voluntary Report Model for Safety Management System (SMS)
    """

    # Anonymous Choices
    ANONYMOUS_CHOICES = [
        ('YES', 'SI'),
        ('NO', 'NO'),
    ]

    # Role Choices
    ROLE_CHOICES = [
        ('DIRECTOR', 'Dirección'),
        ('OPERATIONS', 'Operaciones'),
        ('GROUND_INSTRUCTOR', 'Instructor de tierra'),
        ('FLIGHT_INSTRUCTOR', 'Instructor de vuelo'),
        ('STUDENT', 'Alumno'),
        ('ADMIN', 'Administrativo'),
        ('OTHER', 'Otro'),
    ]

    # Status Choices for AI Analysis
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente de análisis'),
        ('PROCESSING', 'Analizando con IA'),
        ('COMPLETED', 'Análisis completado'),
        ('FAILED', 'Error en análisis'),
    ]

    # Area Choices
    AREA_CHOICES = [
        ('ADMIN', 'Sede administrativa'),
        ('PLATFORM', 'Plataforma'),
        ('AIRPORT_OFFICE', 'Ofic. Aeropuerto'),
        ('OPERATIONS', 'Operaciones'),
        ('OTHER', 'Otro'),
    ]
    
    # Report data.
    is_anonymous = models.CharField(
        max_length=3,
        choices=ANONYMOUS_CHOICES,
        default='NO',
        verbose_name="Reporte anónimo"
    )
    first_name = models.CharField(
        max_length=200, 
        verbose_name="Nombre",
        blank=True,
        null=True
    )
    last_name = models.CharField(
        max_length=200, 
        verbose_name="Apellido",
        blank=True,
        null=True
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES,
        default='',
        verbose_name="Cargo o función",
        blank=True,
        null=True
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name="Fecha"
    )
    time = models.TimeField(
        default=timezone.localtime,
        verbose_name="Hora",
    )

    # Area of danger.
    area = models.CharField(
        max_length=20,
        choices=AREA_CHOICES,
        default='OPERATIONS',
        verbose_name="Área del peligro"
    )

    # Description of danger.
    description = models.TextField(
        max_length=1000,
        verbose_name="Descripción del peligro"
    )

    # AI Analysis Status
    ai_analysis_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Estado del análisis de IA",
        db_index=True  # Database index for fast queries
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
        blank=True,
        null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Reporte voluntario"
        verbose_name_plural = "Reportes voluntarios"
        
    def __str__(self):
        return "{} {}".format(self.date, self.area)
    
    def has_ai_analysis(self):
        """Check if this report has a completed AI analysis"""
        return hasattr(self, 'report_analysis') and self.ai_analysis_status == 'COMPLETED'
    
class ReportAnalysis(models.Model):
    """
    Report Analysis Model for Safety Management System (SMS)
    """

    # Area Choices
    VALIDITY_CHOICES = [
        ('YES', 'SI'),
        ('NO', 'NO'),
    ]

    report = models.ForeignKey(
        VoluntaryReport,
        on_delete=models.CASCADE,
    )
    is_valid = models.CharField(
        max_length=3,
        choices=VALIDITY_CHOICES,
        default='NO',
        verbose_name="Es válido"
    )
    severity = models.CharField(
        max_length=1,
        verbose_name="Nivel de severidad"
    )
    probability = models.CharField(
        max_length=1,
        verbose_name="Nivel de probabilidad"
    )
    value = models.CharField(
        max_length=2,
        verbose_name="Valor alfanumérico",
        help_text="Combinación de severidad y probabilidad (ej: C4, D3)"
    )
    risk_analysis = models.JSONField(
        verbose_name="Análisis de riesgos",
        default=list,
        help_text="Lista de análisis de riesgos con relevance y text"
    )
    recommendations = models.JSONField(
        verbose_name="Recomendaciones",
        default=list,
        help_text="Lista de recomendaciones con relevance y text"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de análisis",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Análisis de reporte"
        verbose_name_plural = "Análisis de reportes"
        
    def __str__(self):
        return "{} {}".format(self.report.date, self.report.area)
    
    def get_risk_analysis_by_relevance(self, relevance):
        """Get risk analysis items filtered by relevance level"""
        if not self.risk_analysis:
            return []
        return [item for item in self.risk_analysis if item.get('relevance') == relevance]
    
    def get_recommendations_by_relevance(self, relevance):
        """Get recommendations filtered by relevance level"""
        if not self.recommendations:
            return []
        return [item for item in self.recommendations if item.get('relevance') == relevance]
    
    def get_high_priority_risks(self):
        """Get high priority risk analysis items"""
        return self.get_risk_analysis_by_relevance('high')
    
    def get_high_priority_recommendations(self):
        """Get high priority recommendations"""
        return self.get_recommendations_by_relevance('high')