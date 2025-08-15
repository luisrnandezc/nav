from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class voluntary_report(models.Model):
    """
    Voluntary Report Model for Safety Management System (SMS)
    """

    # Area Choices
    AREA_CHOICES = [
        ('ADMIN', 'Sede administrativa'),
        ('PLATFORM', 'Plataforma'),
        ('AIRPORT_OFFICE', 'Ofic. Aeropuerto'),
        ('OPERATIONS', 'Operaciones'),
        ('OTHER', 'Otro'),
    ]
    
    # Report data.
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
        max_length=200, 
        verbose_name="Cargo o función que ocupa en la institución",
        blank=True,
        null=True
    )
    date = models.DateField(
        verbose_name="Fecha"
    )
    time = models.TimeField(
        verbose_name="Hora"
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

    class Meta:
        verbose_name = "Reporte voluntario"
        verbose_name_plural = "Reportes voluntarios"
        
    def __str__(self):
        return f"{self.date} {self.area}"
    
class report_analysis(models.Model):
    """
    Report Analysis Model for Safety Management System (SMS)
    """

    report = models.ForeignKey(
        voluntary_report,
        on_delete=models.CASCADE,
    )
    is_valid = models.BooleanField(
        verbose_name="¿Es un reporte de seguridad válido?"
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
    risk_analysis = models.TextField(
        verbose_name="Análisis de riesgos",
        max_length=5000,
    )
    recommendations = models.TextField(
        verbose_name="Recomendaciones",
        max_length=5000,
    )

    class Meta:
        verbose_name = "Análisis de reporte"
        verbose_name_plural = "Análisis de reportes"
        
    def __str__(self):
        return f"{self.report.date} {self.report.area}"