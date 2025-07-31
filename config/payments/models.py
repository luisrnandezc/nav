from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

class StudentPayment(models.Model):
    """Model for tracking student payments, balances, and payment confirmations."""

    #region CHOICE DEFINITIONS

    # Payment type
    FLIGHT = 'VUELO'
    SIMULATOR = 'SIMULADOR'

    PAYMENT_TYPES = [
        (FLIGHT, 'Vuelo'),
        (SIMULATOR, 'Simulador'),
    ]
    #endregion

    #region MODEL FIELDS
    student_profile = models.ForeignKey(
        'accounts.StudentProfile', 
        on_delete=models.CASCADE, 
        related_name='payments',
        verbose_name='Estudiante',
    )
    amount = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Monto',
    )
    type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPES,
        default=FLIGHT,
        verbose_name='Tipo de pago',
    )
    date_added = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Fecha de pago'
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'role': 'STAFF'},
        verbose_name='Agregado por',
    )
    confirmed = models.BooleanField(
        default=False, 
        verbose_name='Confirmado'
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_student_payments',
        limit_choices_to={'staff_profile__can_confirm_payments': True},
        verbose_name='Confirmado por',
    )
    confirmation_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de confirmación',
    )
    notes = models.TextField(
        blank=True, 
        verbose_name='Notas'
    )
    #endregion

    class Meta:
        db_table = 'student_payments'
        ordering = ['-date_added', 'student_profile__user__national_id']
        verbose_name = 'Pago de Estudiante'
        verbose_name_plural = 'Pagos de Estudiantes'

    def __str__(self):
        return f"{self.student_profile.user.first_name} {self.student_profile.user.last_name} - ${self.amount}"

    def get_student_full_name(self):
        """Return the student's full name for admin display"""
        return f"{self.student_profile.user.first_name} {self.student_profile.user.last_name}"
    get_student_full_name.short_description = 'Estudiante'
    get_student_full_name.admin_order_field = 'student_profile__user__last_name'

    def clean(self):
        """Validate payment data"""
        if self.amount <= 0:
            raise ValidationError('El monto debe ser mayor a cero')
        
        # Validate that added_by is a staff member
        if self.added_by and self.added_by.role != 'STAFF':
            raise ValidationError('Solo el personal autorizado puede agregar pagos')
        
        if self.confirmed_by and (
            not hasattr(self.confirmed_by, 'staff_profile') or 
            not self.confirmed_by.staff_profile.can_confirm_payments
        ):
            raise ValidationError('Solo el personal autorizado puede confirmar pagos')

    def confirm(self, user):
        """Call this method when a director confirms the payment"""
        if not hasattr(user, 'staff_profile') or not user.staff_profile.can_confirm_payments:
            raise ValidationError('Solo el personal autorizado puede confirmar pagos')
            
        self.confirmed = True
        self.confirmed_by = user
        self.confirmation_date = timezone.now()
        self.save()
        
        # Update balance if your StudentProfile has one
        if self.type == 'VUELO':
            self.student_profile.flight_balance += self.amount
        elif self.type == 'SIMULADOR':
            self.student_profile.sim_balance += self.amount
            self.student_profile.save()
    
    def save(self, *args, **kwargs):
        """Override save method to validate data before saving"""
        # Automatically update confirmation_date if confirmed is set to True
        if self.confirmed and not self.confirmation_date:
            self.confirmation_date = timezone.now()
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override delete method to validate data before deleting"""
        # Automatically update balance if your StudentProfile has one
        if self.type == 'VUELO':
            self.student_profile.flight_balance -= self.amount
        elif self.type == 'SIMULADOR':
            self.student_profile.sim_balance -= self.amount
        self.student_profile.save()
        super().delete(*args, **kwargs)
