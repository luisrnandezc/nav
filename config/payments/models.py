from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

class StudentPayment(models.Model):
    """Model for tracking student payments, balances, and payment confirmations."""

    #region CHOICE DEFINITIONS

    # Payment type
    FLIGHT = 'VUELO'
    SIMULATOR = 'SIMULADOR'
    DEBIT = 'DEBITO'

    PAYMENT_TYPES = [
        (FLIGHT, 'Vuelo'),
        (SIMULATOR, 'Simulador'),
        (DEBIT, 'Débito'),
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
        verbose_name='Monto',
    )
    type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPES,
        default=FLIGHT,
        verbose_name='Tipo de pago',
    )
    date_added = models.DateField(
        default=timezone.now,
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
        # The save() method will handle balance updates
        self.save()
    
    def unconfirm(self):
        """Call this method when a payment is unconfirmed"""
        self.confirmed = False
        self.confirmed_by = None
        self.confirmation_date = None
        # The save() method will handle balance updates
        self.save()
    
    def _update_student_balance(self, add=True):
        """Helper method to update student balance"""
        # Refresh the student profile from database to get current balance
        self.student_profile.refresh_from_db()
        
        if self.type == 'VUELO' or self.type == 'DEBITO':
            if add:
                self.student_profile.flight_balance += self.amount
            else:
                self.student_profile.flight_balance -= self.amount
        elif self.type == 'SIMULADOR':
            if add:
                self.student_profile.sim_balance += self.amount
            else:
                self.student_profile.sim_balance -= self.amount
        else:
            return
            
        self.student_profile.save()
    
    def save(self, *args, **kwargs):
        """Override save method to handle balance updates and validation"""
        # Get the original object from the database if this is an existing payment
        original_obj = None
        if hasattr(self, 'pk') and self.pk:
            try:
                original_obj = StudentPayment.objects.get(pk=self.pk)
            except StudentPayment.DoesNotExist:
                pass
        
        # Automatically update confirmation_date if confirmed is set to True
        if self.confirmed and not self.confirmation_date:
            self.confirmation_date = timezone.now()
        
        # Handle balance updates based on confirmation status changes
        if original_obj:
            # Existing payment being modified
            if not original_obj.confirmed and self.confirmed:
                # Payment being confirmed - add to balance
                self._update_student_balance(add=True)
            elif original_obj.confirmed and not self.confirmed:
                # Payment being unconfirmed - subtract from balance
                self._update_student_balance(add=False)
        else:
            # New payment - only update balance if it's confirmed
            if self.confirmed:
                self._update_student_balance(add=True)
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override delete method to validate data before deleting"""
        # Get the original object from the database before deletion
        if hasattr(self, 'pk') and self.pk:
            try:
                original_obj = StudentPayment.objects.get(pk=self.pk)
                if original_obj.confirmed:
                    # Use the original object to call the helper method
                    original_obj._update_student_balance(add=False)
            except StudentPayment.DoesNotExist:
                pass
        super().delete(*args, **kwargs)
