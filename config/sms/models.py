from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.conf import settings
from datetime import timedelta, date
import json


class VoluntaryReport(models.Model):
    """
    Voluntary Report Model for Safety Management System (SMS)
    """

    #region Choices
    ANONYMOUS_CHOICES = [
        ('YES', 'SI'),
        ('NO', 'NO'),
    ]

    ROLE_CHOICES = [
        ('DIRECTOR', 'Dirección'),
        ('OPERATIONS', 'Operaciones'),
        ('GROUND_INSTRUCTOR', 'Instructor de tierra'),
        ('FLIGHT_INSTRUCTOR', 'Instructor de vuelo'),
        ('STUDENT', 'Alumno'),
        ('ADMIN', 'Administrativo'),
        ('OTHER', 'Otro'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pendiente de análisis'),
        ('PROCESSING', 'Analizando con IA'),
        ('COMPLETED', 'Análisis completado'),
        ('FAILED', 'Error en análisis'),
    ]

    AREA_CHOICES = [
        ('ADMIN', 'Sede administrativa'),
        ('PLATFORM', 'Plataforma'),
        ('AIRPORT_OFFICE', 'Ofic. Aeropuerto'),
        ('OPERATIONS', 'Operaciones'),
        ('OTHER', 'Otro'),
    ]
    #endregion
    
    #region Fields
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
    area = models.CharField(
        max_length=20,
        choices=AREA_CHOICES,
        default='OPERATIONS',
        verbose_name="Área del peligro"
    )
    description = models.TextField(
        max_length=1000,
        verbose_name="Descripción del peligro"
    )
    ai_analysis_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Estado del análisis de IA",
        db_index=True  # Database index for fast queries
    )
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
    #endregion

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

    VALIDITY_CHOICES = [
        ('YES', 'SI'),
        ('NO', 'NO'),
    ]

    #region Fields
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
        verbose_name="Severidad"
    )
    probability = models.CharField(
        max_length=1,
        verbose_name="Probabilidad"
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
    actions_created = models.BooleanField(
        default=False,
        verbose_name="Acciones creadas"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de análisis",
        blank=True,
        null=True
    )
    #endregion

    class Meta:
        verbose_name = "Análisis de reporte"
        verbose_name_plural = "Análisis de reportes"
        
    def __str__(self):
        return "{} {}".format(self.report.date, self.report.area)


class SMSAction(models.Model):
    """
    SMS Action Model for Safety Management System (SMS)
    """

    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('IN_PROGRESS', 'En progreso'),
        ('COMPLETED', 'Completada'),
        ('OVERDUE', 'Vencida'),
    ]

    #region Fields
    report = models.ForeignKey(
        ReportAnalysis,
        on_delete=models.CASCADE,
        verbose_name="Reporte"
    )
    description = models.CharField(
        max_length=1000,
        verbose_name="Descripción"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Estatus"
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'STAFF'},
        verbose_name="Asignado a"
    )
    due_date = models.DateField(
        verbose_name="Vencimiento",
        blank=True,
        null=True
    )
    created_at = models.DateField(
        auto_now_add=True,
        verbose_name="Creación"
    )
    #endregion

    class Meta:
        verbose_name = "Acción de SMS"
        verbose_name_plural = "Acciones de SMS"
    
    def is_overdue(self):
        """Check if the action is overdue"""
        if self.due_date is None:
            return True
        return self.due_date < date.today()

    def __str__(self):
        return "{} {} {}".format(self.report.value, self.status, self.due_date)
    
    @classmethod
    def create_actions_from_recommendations(cls, report_analysis):
        """
        Create SMSAction objects from the recommendations of a ReportAnalysis.
        One action is created for each recommendation.
        """
        if not report_analysis.recommendations:
            return []
        
        actions_created = []
        for recommendation in report_analysis.recommendations:
            action = cls.objects.create(
                report=report_analysis,
                description=recommendation.get('text', ''),
                status='PENDING',
                assigned_to=None,  # Can be assigned later
                due_date=None      # Can be set later
            )
            actions_created.append(action)
        
        # Mark that actions have been created for this report analysis
        report_analysis.actions_created = True
        report_analysis.save()
        
        return actions_created