from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

class StudentTransaction(models.Model):
    """Model for tracking student transactions, balances, and transaction confirmations."""

    #region CHOICE DEFINITIONS

    # Transaction type
    CREDIT = 'CREDITO'
    DEBIT = 'DEBITO'

    TRANSACTION_TYPES = [
        (CREDIT, 'Crédito'),
        (DEBIT, 'Débito'),
    ]

    # Transaction category
    NA = 'N/A'
    FLIGHT = 'VUELO'
    SIMULATOR = 'SIMULADOR'
    MATERIAL = 'MATERIAL'
    OTHER = 'OTRO'

    TRANSACTION_CATEGORIES = [
        (NA, 'N/A'),
        (FLIGHT, 'Vuelo'),
        (SIMULATOR, 'Simulador'),
        (MATERIAL, 'Material'),
        (OTHER, 'Otro'),
    ]
    #endregion

    #region MODEL FIELDS
    student_profile = models.ForeignKey(
        'accounts.StudentProfile', 
        on_delete=models.CASCADE, 
        related_name='transactions',
        verbose_name='Estudiante',
    )
    amount = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name='Monto',
        validators=[MinValueValidator(0)],
    )
    type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        default=CREDIT,
        verbose_name='Tipo de transacción',
    )
    category = models.CharField(
        max_length=20,
        choices=TRANSACTION_CATEGORIES,
        default=NA,
        verbose_name='Categoría de transacción',
    )
    date_added = models.DateField(
        default=timezone.now,
        verbose_name='Fecha de transacción'
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
        related_name='confirmed_student_transactions',
        limit_choices_to={'staff_profile__can_confirm_transactions': True},
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
        db_table = 'student_transactions_db'
        ordering = ['-date_added', 'student_profile__user__national_id']
        verbose_name = 'Transacción de Estudiante'
        verbose_name_plural = 'Transacciones de Estudiantes'

    def __str__(self):
        return f"{self.student_profile.user.first_name} {self.student_profile.user.last_name} - ${self.amount} - {self.type} - {self.category}"

    def get_student_full_name(self):
        """Return the student's full name for admin display"""
        return f"{self.student_profile.user.first_name} {self.student_profile.user.last_name}"
    get_student_full_name.short_description = 'Estudiante'
    get_student_full_name.admin_order_field = 'student_profile__user__last_name'

    def clean(self):
        """Validate transaction data"""
        
        # Validate that added_by is a staff member
        if self.added_by and self.added_by.role != 'STAFF':
            raise ValidationError('Solo el personal autorizado puede agregar transacciones')
        
        if self.confirmed_by and (
            not hasattr(self.confirmed_by, 'staff_profile') or 
            not self.confirmed_by.staff_profile.can_confirm_transactions
        ):
            raise ValidationError('Solo el personal autorizado puede confirmar transacciones')

    def confirm(self, user):
        """Call this method when a director confirms the transaction"""
        if not hasattr(user, 'staff_profile') or not user.staff_profile.can_confirm_transactions:
            raise ValidationError('Solo el personal autorizado puede confirmar transacciones')
            
        self.confirmed = True
        self.confirmed_by = user
        self.confirmation_date = timezone.now()
        # The save() method will handle balance updates
        self.save()
    
    def unconfirm(self):
        """Call this method when a transaction is unconfirmed"""
        self.confirmed = False
        self.confirmed_by = None
        self.confirmation_date = None
        # The save() method will handle balance updates
        self.save()
    
    def _update_student_balance(self, add=True):
        """Helper method to update student balance"""
        # Refresh the student profile from database to get current balance
        self.student_profile.refresh_from_db()
        
        if self.type == 'CREDITO':
            if add:
                self.student_profile.balance += self.amount
            else:
                self.student_profile.balance -= self.amount
        elif self.type == 'DEBITO':
            if add:
                self.student_profile.balance -= self.amount
            else:
                self.student_profile.balance += self.amount
        else:
            return
            
        self.student_profile.save()
    
    def save(self, *args, **kwargs):
        """Override save method to handle balance updates and validation"""
        # Get the original object from the database if this is an existing payment
        original_obj = None
        if hasattr(self, 'pk') and self.pk:
            try:
                original_obj = StudentTransaction.objects.get(pk=self.pk)
            except StudentTransaction.DoesNotExist:
                pass
        
        # Automatically update confirmation_date if confirmed is set to True
        if self.confirmed and not self.confirmation_date:
            self.confirmation_date = timezone.now()
        
        # Handle balance updates based on confirmation status changes
        if original_obj:
            # Existing transaction being modified
            if not original_obj.confirmed and self.confirmed:
                # Transaction being confirmed - add to balance
                self._update_student_balance(add=True)
            elif original_obj.confirmed and not self.confirmed:
                # Transaction being unconfirmed - subtract from balance
                self._update_student_balance(add=False)
        else:
            # New transaction - only update balance if it's confirmed
            if self.confirmed:
                self._update_student_balance(add=True)
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override delete method to validate data before deleting a transaction"""
        # Get the original object from the database before deletion
        if hasattr(self, 'pk') and self.pk:
            try:
                original_obj = StudentTransaction.objects.get(pk=self.pk)
                if original_obj.confirmed:
                    # Use the original object to call the helper method to update the student balance
                    original_obj._update_student_balance(add=False)
            except StudentTransaction.DoesNotExist:
                pass
        super().delete(*args, **kwargs)
