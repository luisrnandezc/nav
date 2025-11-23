from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.conf import settings
from datetime import timedelta, date
import json


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
    ai_analysis_result = models.JSONField(
        default=dict,
        verbose_name="Resultado del análisis de IA",
        blank=True,
        null=True
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