from django.db import models, transaction
from django.utils.timezone import localdate
from datetime import timedelta
from django.core.exceptions import ValidationError
from accounts.models import StudentProfile
from fleet.models import Aircraft

class FlightPeriod(models.Model):
    """Periodo de vuelo"""
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
        related_name="flight_periods",
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

    def generate_slots(self):
        """
        Create FlightSlot objects for each day, each block, and each aircraft.
        """
        from scheduler.models import FlightSlot

        blocks = ['AM', 'M', 'PM']
        aircraft = self.aircraft
        created = 0
        
        # Generate slots for the entire period (from start_date to end_date)
        today = localdate()
        current_date = self.start_date
        while current_date <= self.end_date:
            status = 'available'
            if current_date < today:
                status = 'unavailable'
            for block in blocks:
                FlightSlot.objects.create(
                    flight_period=self,
                    date=current_date,
                    block=block,
                    aircraft=aircraft,
                    status=status
                )
                created += 1
            current_date += timedelta(days=1)

        return created
    
    def _check_flight_period_length(self, start_date, end_date):
        """Check if the flight period length is a multiple of 7 days."""
        period_days = (end_date - start_date).days + 1
        if period_days % 7 != 0:
            raise ValidationError("El periodo debe ser un múltiplo de 7 días (1 semana, 2 semanas, etc.).")
        
    def _check_flight_period_length_limits(self, start_date, end_date):
        """Check if the flight period length is no less than 7 days and no more than 21 days."""
        period_days = (end_date - start_date).days + 1
        if period_days < 7 or period_days > 21:
            raise ValidationError("El período no puede ser menor a 7 días ni mayor a 3 semanas (21 días).")
    
    def _check_flight_period_overlap(self, start_date, end_date, aircraft):
        """Check if the flight period overlaps with another flight period."""
        existing_periods = FlightPeriod.objects.filter(aircraft=aircraft, start_date__lte=end_date, end_date__gte=start_date)
        
        # Exclude the current instance if it's being updated
        if self.pk:
            existing_periods = existing_periods.exclude(pk=self.pk)
            
        if existing_periods.exists():
            for existing_period in existing_periods:
                if start_date <= existing_period.end_date and end_date >= existing_period.start_date:
                    raise ValidationError("El período se superpone con otro período de vuelo.")
    
    def _check_aircraft_availability(self, aircraft):
        """Check if the aircraft is available."""
        if aircraft not in Aircraft.objects.filter(is_active=True, is_available=True):
            raise ValidationError("La aeronave no está activa o disponible.")
    
    def _check_reasonable_date_range(self, start_date):
        """Check if the date range is reasonable."""
        from datetime import date, timedelta
        max_future_date = date.today() + timedelta(days=30)
        if start_date > max_future_date:
            raise ValidationError("La fecha de inicio no puede ser más de 30 días en el futuro.")

    def clean(self):
        super().clean()
        
        start_date = self.start_date
        end_date = self.end_date
        aircraft = self.aircraft

        self._check_flight_period_length(start_date, end_date)
        self._check_flight_period_length_limits(start_date, end_date)
        self._check_flight_period_overlap(start_date, end_date, aircraft)
        self._check_aircraft_availability(aircraft)
        self._check_reasonable_date_range(start_date)
    
    def __str__(self):
        return f"Periodo: {self.start_date} → {self.end_date}"
    
    class Meta:
        verbose_name = "Periodo de vuelo"
        verbose_name_plural = "Periodos de vuelo"
        ordering = ['-start_date']

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class FlightSlot(models.Model):
    """Slot de vuelo"""

    #region choices definitions
    BLOCK_CHOICES = [
        ('AM', 'AM'),
        ('M', 'M'),
        ('PM', 'PM'),
    ]

    # available: the slot is available for scheduling.
    # pending: there is a flight request for this slot.
    # reserved: there is an approved flight request for this slot.
    # unavailable: the slot is unavailable for scheduling because of maintenance, weather, etc.

    STATUS_CHOICES = [
        ('available', 'L'),
        ('pending', 'P'),
        ('reserved', 'R'),
        ('unavailable', 'NA'),
    ]
    #endregion

    #region model fields
    flight_period = models.ForeignKey(
        'scheduler.FlightPeriod',
        on_delete=models.CASCADE,
        related_name="slots",
        verbose_name="Periodo de vuelo",
        help_text="Periodo de vuelo del slot",
    )
    date = models.DateField(
        verbose_name="Fecha",
        help_text="Fecha del slot",
        default=localdate
    )
    block = models.CharField(
        verbose_name="Bloque",
        help_text="Bloque del slot",
        choices=BLOCK_CHOICES,
        max_length=2
    )
    instructor = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        related_name="instructor_flight_slots",
        limit_choices_to={'role': 'INSTRUCTOR'},
        null=True,
        blank=True,
        verbose_name="Instructor",
        help_text="Instructor del slot",
    )
    student = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        related_name="student_flight_slots",
        limit_choices_to={'role': 'STUDENT'},
        null=True,
        blank=True,
        verbose_name="Estudiante",
        help_text="Estudiante del slot",
    )
    aircraft = models.ForeignKey(
        'fleet.Aircraft',
        on_delete=models.SET_NULL,
        related_name="flight_slots",
        limit_choices_to={'is_active': True, 'is_available': True},
        null=True,
        blank=True,
        verbose_name="Aeronave",
        help_text="Aeronave del slot",
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        null=False,
        blank=False,
        default='available',
        verbose_name="Estatus",
        help_text="Estatus del slot",
    )
    #endregion

    class Meta:
        unique_together = ('date', 'block', 'aircraft')  # only one slot per date, block and aircraft
        verbose_name = "Slot de vuelo"
        verbose_name_plural = "Slots de vuelo"
        ordering = ['date', 'block', 'aircraft']

    def __str__(self):
        aircraft_str = self.aircraft.registration if self.aircraft else "Sin aeronave"
        return f"{self.date} - {aircraft_str} ({self.get_status_display()}) - Bloque {self.get_block_display()}"
    
class FlightRequest(models.Model):
    """Solicitud de vuelo"""

    #region choices definitions
    STATUS_CHOICES = [
        ('pending', 'En revisión'),
        ('approved', 'Aprobada'),
        ('cancelled', 'Cancelada'),
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
        related_name="flight_requests",
        verbose_name="Slot de vuelo",
        help_text="Slot de vuelo de la solicitud",
    )
    status = models.CharField(
        max_length=15, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="Estatus",
        help_text="Estatus de la solicitud",
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

    def create_request(self, student, slot):
        """Create a flight request and update the slot status to unavailable."""
        with transaction.atomic():
            if slot.status != 'available':
                raise ValidationError("El slot no está disponible")
            if slot.flight_period.is_active != True:
                raise ValidationError("El período de vuelo no está activo")
            # Create the flight request
            flight_request = FlightRequest(
                student=student,
                slot=slot,
                status='pending'
            )
            # Update slot status to pending
            slot.status = 'pending'
            slot.student = student
            slot.save()
            # Update the instance for consistency
            self.student = student
            self.slot = slot
            self.status = 'pending'
            self.pk = flight_request.pk
            self.save()

    def approve(self, original_status=None):
        """Approve the flight request and update the slot status to reserved."""
        # Check if we can approve (use original_status if provided, otherwise current status)
        status_to_check = original_status if original_status is not None else self.status
        if status_to_check != 'pending':
            raise ValidationError("Solo solicitudes pendientes pueden ser aprobadas")
        
        # Check if the slot is pending
        if self.slot.status == 'pending' and self.slot.student != self.student:
            raise ValidationError("Ya hay una solicitud de vuelo pendiente para este slot")
        
        # Check if the slot is reserved
        if self.slot.status == 'reserved':
            raise ValidationError("Ya hay una solicitud de vuelo aprobada para este slot")
        
        # Secondary balance check (safety net)
        try:
            balance = self.student.student_profile.balance
            if balance < 500.00 and not (self.student.student_profile.has_credit or self.student.student_profile.has_temp_permission):
                raise ValidationError(f"Balance insuficiente para aprobar. Balance actual: ${balance:.2f}")
        except StudentProfile.DoesNotExist:
            raise ValidationError("No se pudo verificar el balance del estudiante: Perfil de estudiante no encontrado")

        with transaction.atomic():
            # Update flight request status
            self.status = 'approved'
            self.save()
            
            # Update slot status to reserved
            self.slot.status = 'reserved'
            self.slot.student = self.student
            self.slot.save()

             # Update student profile has_temp_permission to False
            if self.student.student_profile.has_temp_permission:
                self.student.student_profile.has_temp_permission = False
                self.student.student_profile.save()
    
    def cancel(self, apply_fee=False):
        """Cancel the flight request and free up the slot."""
        if self.status not in ['pending', 'approved']:
            raise ValidationError("Solo solicitudes pendientes o aprobadas pueden ser canceladas")
        
        with transaction.atomic():
            # Update flight request status and timestamp using update() to bypass clean validation
            # since we're in a controlled transaction and will free up the slot immediately
            from django.utils import timezone
            FlightRequest.objects.filter(pk=self.pk).update(
                status='cancelled',
                updated_at=timezone.now()
            )
            self.status = 'cancelled'  # Update the instance for consistency
            self.updated_at = timezone.now()  # Update the instance timestamp for consistency
            
            # Free up the slot
            self.slot.status = 'available'
            self.slot.student = None
            self.slot.save()

            # Apply fee if apply_fee is True
            if apply_fee:
                self.student.student_profile.balance -= self.slot.flight_period.aircraft.hourly_rate
                self.student.student_profile.save()

    def clean(self):
        # Student balance must be at least $500
        try:
            balance = self.student.student_profile.balance
        except StudentProfile.DoesNotExist:
            raise ValidationError("No se pudo verificar el balance del estudiante: Perfil de estudiante no encontrado")
        if balance < 500.00:
            if self.student.student_profile.has_credit or self.student.student_profile.has_temp_permission:
                pass
            else:
                raise ValidationError(f"Balance insuficiente (${balance:.2f}). Se requiere un mínimo de $500")
        
        # Limit requests by balance
        if  balance < 500.00 and (self.student.student_profile.has_credit or self.student.student_profile.has_temp_permission):
            max_requests = 1
        else:
            max_requests = balance // 500
        existing_requests = FlightRequest.objects.filter(
            student=self.student, status__in=["pending", "approved"]
        ).exclude(pk=self.pk)
        if existing_requests.count() >= max_requests:
            raise ValidationError(f"Ya tiene el máximo de {max_requests} solicitudes de vuelo aprobadas o pendientes")
        
    def delete(self, *args, **kwargs):
        """Delete the flight request and free up the slot."""
        with transaction.atomic():
            slot = self.slot
            if slot.status in ['pending', 'reserved', 'unavailable'] or slot.student:
                slot.status = 'available'
                slot.student = None
                slot.save()
            super().delete(*args, **kwargs)

    def __str__(self):
        return f"Solicitud de vuelo. Estudiante: {self.student} - Estatus: {self.get_status_display()}"
    
    class Meta:
        verbose_name = "Solicitud de vuelo"
        verbose_name_plural = "Solicitudes de vuelo"
        ordering = ['-requested_at']
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class CancellationsFee(models.Model):
    """Model for tracking cancellation fees."""

    #region model fields
    flight_request = models.ForeignKey(
        'scheduler.FlightRequest',
        on_delete=models.SET_NULL,
        related_name="cancellations_fees",
        verbose_name="Solicitud de vuelo",
        help_text="Solicitud de vuelo de la multa",
        null=True,
        blank=True,
    )
    amount = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        verbose_name="Monto",
        help_text="Monto de la multa",
    )
    date_added = models.DateField(
        default=localdate,
        verbose_name="Fecha de adición",
    )
    #endregion

    def delete(self, *args, **kwargs):
        """Delete the cancellation fee and reimburse the student."""
        if self.flight_request and self.flight_request.student:
            student = self.flight_request.student
            reimbursement_amount = self.amount
            
            # Refund the fee back to the student's balance
            try:
                student.student_profile.balance += reimbursement_amount
                student.student_profile.save()
                
            except Exception as e:
                raise ValidationError(f"Error al reembolsar la multa: {str(e)}")
        
        # Delete the fee record
        super().delete(*args, **kwargs)
    
    def __str__(self):
        return f"Multa por cancelación extemporánea. Solicitud de vuelo: {self.flight_request} - Monto: {self.amount}"
    
    class Meta:
        verbose_name = "Multa por cancelación"
        verbose_name_plural = "Multas por cancelación"
        ordering = ['-date_added']
        