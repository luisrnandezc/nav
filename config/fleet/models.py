from django.db import models
from django.contrib.auth.models import User

class Aircraft(models.Model):

    # Basic Information
    manufacturer = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    registration = models.CharField(max_length=255, unique=True)
    serial_number = models.CharField(max_length=255, unique=True)
    year_manufactured = models.IntegerField()

    # Operational status
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    maintenance_status = models.CharField(
        max_length=50,
        choices=[
            ("OPERATIONAL", "Operativo"),
            ("MAINTENANCE", "En mantenimiento"),
            ("OUT_OF_SERVICE", "Fuera de servicio"),
        ],
        default="OPERATIONAL",
    )
    total_hours = models.IntegerField(default=0)
    total_cycles = models.IntegerField(default=0)

    # Scheduling configuration
    max_daily_slots = models.IntegerField(default=3)
    hourly_rate = models.DecimalField(max_digits=4, decimal_places=1, default=120.0)

    # Additional info
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE)
    date = models.DateField()
    is_available = models.BooleanField(default=True)
    reason = models.CharField(max_length=200, blank=True) # "Mantenimiento", "WX", "Reservado"
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['aircraft', 'date']
        ordering = ['date']
        verbose_name = "Disponibilidad de Aeronave"
        verbose_name_plural = "Disponibilidad de Aeronaves"

    def __str__(self):
        status = "Disponible" if self.is_available else "No disponible"
        return f"{self.aircraft.registration} - {self.date}: {status}"
    
class AircraftHours(models.Model):
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT)
    date = models.DateField()
    hours_flown = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    total_hours = models.DecimalField(max_digits=6, decimal_places=1, default=0.0)
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['aircraft', 'date']
        ordering = ['-date']