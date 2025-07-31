from django.db import models
from django.conf import settings

class Simulator(models.Model):

    #region CHOICES DEFINITIONS

    # Simulators
    FPT = 'FPT'
    B737 = 'B737'

    SIMULATOR_CHOICES = [
        (FPT, 'FPT'),
        (B737, 'B737'),
    ]
    #endregion

    #region MODEL DEFINITIONS
    name = models.CharField(
        max_length=255,
        choices=SIMULATOR_CHOICES,
        verbose_name="Nombre"
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name="Activo"
    )
    is_available = models.BooleanField(
        default=True, 
        verbose_name="Disponible"
    )
    hourly_rate = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        default=130.0,
        verbose_name="Precio por hora"
    )
    total_hours = models.DecimalField(
        max_digits=8, 
        decimal_places=1, 
        default=0.0, 
        verbose_name="Horas totales"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Fecha de creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Fecha de actualización"
    )
    #endregion

    class Meta:
        ordering = ['name']
        verbose_name = "Simulador"
        verbose_name_plural = "Simuladores"

    def __str__(self):
        return f"Simulador {self.name} - {self.total_hours} horas"

    @property
    def is_available_for_scheduling(self):
        """Check if simulator can be scheduled"""
        return (self.is_active and 
                self.is_available)

class Aircraft(models.Model):

    # Basic Information
    manufacturer = models.CharField(
        max_length=255,
        verbose_name="Fabricante"
    )
    model = models.CharField(
        max_length=255,
        verbose_name="Modelo"
    )
    registration = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Matrícula"
    )
    serial_number = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Número de serial")
    year_manufactured = models.IntegerField(
        verbose_name="Año de fabricación"
    )

    # Operational status
    is_active = models.BooleanField(
        default=True, 
        verbose_name="Activo"
    )
    is_available = models.BooleanField(
        default=True, 
        verbose_name="Disponible"
    )
    maintenance_status = models.CharField(
        max_length=50,
        choices=[
            ("OPERATIONAL", "Operativo"),
            ("MAINTENANCE", "En mantenimiento"),
            ("OUT_OF_SERVICE", "Fuera de servicio"),
        ],
        default="OPERATIONAL",
        verbose_name="Estatus de mantenimiento"
    )
    total_hours = models.DecimalField(
        max_digits=8, 
        decimal_places=1, 
        default=0.0, 
        verbose_name="Horas totales"
    )

    # Scheduling configuration
    max_daily_slots = models.IntegerField(
        default=3, 
        verbose_name="Slots máximos por día"
    )
    hourly_rate = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        default=130.0,
        verbose_name="Precio por hora"
    )

    # Additional info
    notes = models.TextField(
        blank=True, 
        verbose_name="Notas"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Fecha de creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Fecha de actualización"
    )

    class Meta:
        ordering = ['registration']
        verbose_name = "Aeronave"
        verbose_name_plural = "Aeronaves"

    def __str__(self):
        return f"{self.registration} ({self.manufacturer} {self.model})"

    @property
    def is_available_for_scheduling(self):
        """Check if aircraft can be scheduled"""
        return (self.is_active and 
                self.is_available and 
                self.maintenance_status == "OPERATIONAL")

class AircraftAvailability(models.Model):
    aircraft = models.ForeignKey(
        Aircraft, 
        on_delete=models.CASCADE, 
        verbose_name="Aeronave"
    )
    date = models.DateField(
        verbose_name="Fecha"
    )
    is_available = models.BooleanField(
        default=True, 
        verbose_name="Disponible"
    )
    reason = models.CharField(
        max_length=200, 
        blank=True, 
        verbose_name="Motivo" # "Mantenimiento", "WX", "Reservado"
    )
    notes = models.TextField(
        blank=True, 
        verbose_name="Notas"
    )

    class Meta:
        unique_together = ['aircraft', 'date']
        ordering = ['date']
        verbose_name = "Disponibilidad de Aeronave"
        verbose_name_plural = "Disponibilidad de Aeronaves"

    def __str__(self):
        status = "Disponible" if self.is_available else "No disponible"
        return f"{self.aircraft.registration} - {self.date}: {status}"
    
class AircraftHours(models.Model):
    aircraft = models.ForeignKey(
        Aircraft, 
        on_delete=models.PROTECT, 
        verbose_name="Aeronave"
    )
    date = models.DateField(
        verbose_name="Fecha"
    )
    hours_flown = models.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        default=0.0, 
        verbose_name="Horas voladas"
    )
    total_hours = models.DecimalField(
        max_digits=6, 
        decimal_places=1, 
        default=0.0, 
        verbose_name="Horas totales"
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        verbose_name="Registrado por"
    )
    notes = models.TextField(
        blank=True, 
        verbose_name="Notas"
    )

    class Meta:
        unique_together = ['aircraft', 'date']
        ordering = ['-date']
        verbose_name = "Horas de Aeronave"
        verbose_name_plural = "Horas de Aeronaves"

    def __str__(self):
        return f"{self.aircraft.registration} - {self.date}: {self.total_hours} horas"