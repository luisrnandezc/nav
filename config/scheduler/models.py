from django.db import models
from django.utils import timezone
from datetime import timedelta

class TrainingPeriod(models.Model):
    """Periodo de entrenamiento"""
    start_date = models.DateField(
        verbose_name="Inicio",
        help_text="Inicio",
    )
    end_date = models.DateField(
        verbose_name="Cierre",
        help_text="Cierre",
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name="Activo",
    )
    aircraft = models.ForeignKey(
        'fleet.Aircraft',
        on_delete=models.CASCADE,
        related_name="training_periods",
        verbose_name="Aeronave",
        help_text="Aeronave",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
        help_text="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
        help_text="Fecha de actualización",
    )

    class Meta:
        verbose_name = "Periodo de entrenamiento"
        verbose_name_plural = "Periodos de entrenamiento"
        ordering = ['-start_date']

    def generate_slots(self):
        """
        Create FlightSlot objects for each day, each block, and each aircraft.
        """
        from scheduler.models import FlightSlot

        blocks = ['A', 'B', 'C']
        day = self.start_date
        aircraft = self.aircraft
        created = 0

        while day <= self.end_date:
            for block in blocks:
                FlightSlot.objects.create(
                    training_period=self,
                    date=day,
                    block=block,
                    aircraft=aircraft,
                    status='free'
                )
                created += 1
            day += timedelta(days=1)

        return created

    def __str__(self):
        return f"Ciclo: {self.start_date} → {self.end_date}"

class FlightSlot(models.Model):
    """Sesión de vuelo"""

    #region choices definitions
    BLOCK_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
    ]

    STATUS_CHOICES = [
        ('free', 'Libre'),
        ('pending', 'Pendiente de confirmación'),
        ('confirmed', 'Confirmado'),
        ('cancelled', 'Cancelado'),
    ]
    #endregion

    #region model fields
    training_period = models.ForeignKey(
        'scheduler.TrainingPeriod',
        on_delete=models.CASCADE,
        related_name="slots",
        verbose_name="Periodo de entrenamiento",
        help_text="Periodo de entrenamiento de la sesión",
    )
    date = models.DateField(
        verbose_name="Fecha",
        help_text="Fecha de la sesión",
        default=timezone.now
    )
    block = models.CharField(
        verbose_name="Bloque",
        help_text="Bloque de la sesión",
        choices=BLOCK_CHOICES,
        max_length=1
    )
    instructor = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        related_name="instructor_flight_slots",
        limit_choices_to={'role': 'INSTRUCTOR'},
        null=True,
        blank=True,
        verbose_name="Instructor",
        help_text="Instructor de la sesión",
    )
    student = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        related_name="student_flight_slots",
        limit_choices_to={'role': 'STUDENT'},
        null=True,
        blank=True,
        verbose_name="Estudiante",
        help_text="Estudiante de la sesión",
    )
    aircraft = models.ForeignKey(
        'fleet.Aircraft',
        on_delete=models.SET_NULL,
        related_name="flight_slots",
        limit_choices_to={'is_active': True, 'is_available': True},
        null=True,
        blank=True,
        verbose_name="Aeronave",
        help_text="Aeronave de la sesión",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        null=False,
        blank=False,
        default='free',
        verbose_name="Estado",
        help_text="Estado de la sesión",
    )
    #endregion

    class Meta:
        unique_together = ('date', 'block', 'aircraft')  # only one slot per date, block and aircraft
        verbose_name = "Sesión de vuelo"
        verbose_name_plural = "Sesiones de vuelo"
        ordering = ['date', 'block', 'aircraft']

    def __str__(self):
        aircraft_str = self.aircraft.registration if self.aircraft else "Sin aeronave"
        return f"{self.date} - {aircraft_str} ({self.get_status_display()}) - Bloque {self.get_block_display()}"
    
class FlightRequest(models.Model):
    """Solicitud de vuelo"""

    #region choices definitions
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('cancelled', 'Cancelado'),
    ]
    #endregion

    #region model fields
    student = models.ForeignKey(
        'accounts.User', 
        on_delete=models.CASCADE,
        related_name="flight_requests",
        limit_choices_to={'role': 'STUDENT'},
        verbose_name="Estudiante",
        help_text="Estudiante de la solicitud",
    )
    slot = models.ForeignKey(
        'scheduler.FlightSlot', 
        on_delete=models.CASCADE,
        limit_choices_to={'status': 'free'},
        related_name="flight_requests",
        verbose_name="Sesión de vuelo",
        help_text="Sesión de vuelo de la solicitud",
    )
    flexible = models.BooleanField(
        default=False,
        verbose_name="Flexible",
        help_text="Si es selecciona, el estudiante acepta cualquier bloque en esta fecha",
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    requested_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de solicitud",
        help_text="Fecha de solicitud",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
        help_text="Fecha de actualización",
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas",
        help_text="Notas de la solicitud",
    )
    #endregion

    def __str__(self):
        return f"Solicitud de vuelo. Estudiante: {self.student} - Estado: {self.get_status_display()}"
    
    class Meta:
        verbose_name = "Solicitud de vuelo"
        verbose_name_plural = "Solicitudes de vuelo"
        ordering = ['-requested_at']