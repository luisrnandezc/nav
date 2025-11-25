from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.conf import settings
from datetime import timedelta, date
import json


def default_due_date():
    """Return a date 30 days from today."""
    return timezone.now().date() + timedelta(days=30)


class VoluntaryHazardReport(models.Model):
    """
    Voluntary Hazard Report Model for Safety Management System (SMS)
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
        verbose_name="Anónimo"
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
        verbose_name="Área"
    )
    description = models.TextField(
        max_length=1000,
        verbose_name="Descripción del peligro"
    )
    ai_analysis_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="IA Estatus",
        db_index=True  # Database index for fast queries
    )
    ai_analysis_result = models.JSONField(
        default=dict,
        verbose_name="Resultado del análisis de IA",
        blank=True,
        null=True
    )
    human_validated = models.BooleanField(
        default=False,
        verbose_name="Validado",
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
        verbose_name = "Reporte de peligro voluntario"
        verbose_name_plural = "Reportes de peligro voluntarios"
        
    def __str__(self):
        return "{} {}".format(self.date, self.area)
    
    def has_ai_analysis(self):
        """Check if this report has a completed AI hazard analysis"""
        return self.ai_analysis_status == 'COMPLETED'

    def is_validated_by_human(self):
        """Check if this report is validated by a human"""
        return self.human_validated


class Risk(models.Model):
    """
    Risk Model for Safety Management System (SMS)
    """

    #region Choices
    STATUS_CHOICES = [
        ('NOT_EVALUATED', 'No evaluado'),
        ('INTOLERABLE', 'Intolerable'),
        ('TOLERABLE', 'Tolerable'),
        ('ACCEPTABLE', 'Aceptable'),
    ]

    SEVERITY_CHOICES = [
        ('0', '-'),
        ('A', 'A - Catastrófico'),
        ('B', 'B - Peligroso'),
        ('C', 'C - Grave'),
        ('D', 'D - Leve'),
        ('E', 'E - Insignificante'),
    ]

    PROBABILITY_CHOICES = [
        ('0', '-'),
        ('1', '1 - Sumamente improbable'),
        ('2', '2 - Improbable'),
        ('3', '3 - Remota'),
        ('4', '4 - Ocasional'),
        ('5', '5 - Frecuente'),
    ]
    #endregion

    #region Fields
    report = models.ForeignKey(
        VoluntaryHazardReport, 
        on_delete=models.CASCADE, 
        verbose_name="Reporte Voluntario de Peligro",
        related_name="risks"
    )
    description = models.TextField(
        verbose_name="Descripción",
    )
    pre_evaluation_severity = models.CharField(
        max_length=1,
        choices=SEVERITY_CHOICES,
        default='0',
        verbose_name="Severidad pre-mitigación",
    )
    pre_evaluation_probability = models.CharField(
        max_length=1, 
        choices=PROBABILITY_CHOICES,
        default='0',
        verbose_name="Probabilidad pre-mitigación",
    )
    post_evaluation_severity = models.CharField(
        max_length=1, 
        choices=SEVERITY_CHOICES,
        default='0',
        verbose_name="Severidad post-mitigación",
    )
    post_evaluation_probability = models.CharField(
        max_length=1, 
        choices=PROBABILITY_CHOICES,
        default='0',
        verbose_name="Probabilidad post-mitigación",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NOT_EVALUATED',
        verbose_name="Estatus",
    )
    created_at = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de creación"
    )
    updated_at = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de actualización"
    )
    #endregion

    class Meta:
        verbose_name = "Riesgo"
        verbose_name_plural = "Riesgos"
        
    def __str__(self):
        return "{}".format(self.status)


class MitigationAction(models.Model):
    """
    Mitigation Action Model for Safety Management System (SMS)
    """

    #region Choices
    STATUS_CHOICES = [
        ('PENDING', 'Sin completar'),
        ('COMPLETED', 'Completada'),
        ('EXPIRED', 'Vencida'),
    ]
    #endregion

    #region Fields
    risk = models.ForeignKey(
        Risk, 
        on_delete=models.CASCADE, 
        verbose_name="Riesgo",
        related_name="mitigation_actions"
    )
    description = models.TextField(
        verbose_name="Descripción",
    )
    status=models.CharField(
        max_length=9,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Estatus",
    )
    due_date = models.DateField(
        default=default_due_date,
        verbose_name="Fecha límite"
    )
    notes = models.TextField(
        verbose_name="Notas",
        blank=True,
        null=True
    )
    created_at = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de creación"
    )
    updated_at = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de actualización"
    )
    #endregion

    class Meta:
        verbose_name = "Acción de mitigación"
        verbose_name_plural = "Acciones de mitigación"
        
    def __str__(self):
        return "{} {}".format(self.status, self.due_date)