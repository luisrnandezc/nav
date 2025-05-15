from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, national_id, password=None, **extra_fields):
        if not username:
            raise ValueError("Debe indicar un nombre de usuario")
        if not email:
            raise ValueError("Debe indicar un email válido")
        if not national_id:
            raise ValueError("Debe indicar un ID oficial")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, national_id=national_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, national_id, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, national_id, password, **extra_fields)
    
# Custom User Model
class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Estudiante'
        INSTRUCTOR = 'INSTRUCTOR', 'Instructor'
        STAFF = 'STAFF', 'Staff'
    
    username = models.CharField(max_length=150, unique=True, verbose_name='usuario')
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, verbose_name='Nombre')    
    last_name = models.CharField(max_length=150, verbose_name='Apellido')
    national_id = models.IntegerField(
        validators=[MinValueValidator(999999), MaxValueValidator(100000000)],
        unique=True, 
        verbose_name='Cédula',
    )
    role = models.CharField(max_length=10, choices=Role.choices, verbose_name='Rol')

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'national_id', 'role', 'first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.username})'
    
# Profile Models for Each Role
class StudentProfile(models.Model):
    """Model for managing student information, course enrollment, and flight training progress."""

    #region CHOICE DEFINITIONS

    # Student gender
    MALE = 'M'
    FEMALE = 'F'
    OTHER = 'O'

    STUDENT_GENDER = [
        (MALE, 'M'),
        (FEMALE, 'F'),
        (OTHER, 'Otro'),
    ]

    # Student phase
    GROUND = 'TIERRA'
    FLYING = 'VUELO'

    STUDENT_PHASE = [
        (GROUND, 'Escuela en tierra'),
        (FLYING, 'Línea de vuelo'),
    ]

    # Course type
    COURSE_NA = 'N/A'
    COURSE_PPA = 'PPA'
    COURSE_HVI = 'HVI'
    COURSE_PCA = 'PCA'
    COURSE_IVA = 'IVA'
    COURSE_IVS = 'IVS'
    COURSE_DDV = 'DDV'

    COURSE_TYPES = [
        (COURSE_NA, 'No inscrito'),
        (COURSE_PPA, 'PPA'),
        (COURSE_HVI, 'HVI'),
        (COURSE_PCA, 'PCA'),
        (COURSE_IVA, 'IVA'),
        (COURSE_IVS, 'IVS'),
        (COURSE_DDV, 'DDV'),
    ]

    # Student license
    LICENSE_NA = 'NA'
    LICENSE_AP = 'AP'
    LICENSE_PPA = 'PPA'
    LICENSE_PCA = 'PCA'
    LICENSE_TLA = 'TLA'

    LICENSE_TYPES = [
        (LICENSE_NA, 'N/A'),
        (LICENSE_AP, 'AP'),
        (LICENSE_PPA, 'PPA'),
        (LICENSE_PCA, 'PCA'),
        (LICENSE_TLA, 'TLA'),
    ]

    #endregion

    #region MODEL FIELDS

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')

    student_age = models.PositiveIntegerField(
        validators=[MinValueValidator(16), MaxValueValidator(100)],
        verbose_name='Edad',
        default=None,
    )

    student_gender = models.CharField(
        max_length=1,
        choices=STUDENT_GENDER, 
        default=MALE,
        verbose_name='Género',
    )

    student_phase = models.CharField(
        max_length=20, 
        choices=STUDENT_PHASE, 
        default=GROUND,
        verbose_name='Fase de entrenamiento',
    )
    
    student_license_type = models.CharField(
        max_length=3,
        choices=LICENSE_TYPES,
        default=LICENSE_NA,
        verbose_name='Tipo de licencia',
    )

    student_balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name='Balance para Línea de Vuelo',
    )

    #endregion

    class Meta:
        db_table = 'students_db'
        ordering = ['user__national_id']
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'

    def __str__(self):
        return f'{self.user.username} [ID: {self.user.national_id}] ({self.student_phase} - {self.current_course_type})'
    
    @property
    def current_course_type(self):
        """Get the current course type code or 'N/A' if not enrolled."""
        from academic.models import CourseEdition
        current_course = CourseEdition.objects.filter(students=self.user).order_by('-start_date').first()
        return current_course.course_type.code if current_course else self.COURSE_NA

    @property
    def current_course_edition(self):
        """Get the current course edition number or None if not enrolled."""
        from academic.models import CourseEdition
        current_course = CourseEdition.objects.filter(students=self.user).order_by('-start_date').first()
        return current_course.edition if current_course else None

    def get_total_flying_time(self):
        """
        Calculate total flight time from the FlightLog table.
        """
        total_time = self.flightlog_set.aggregate(models.Sum('flight_hours'))['flight_hours__sum'] or 0
        return total_time
    
    def get_current_course(self):
        """
        Get the student's current course edition.
        Returns None if not enrolled in any course.
        """
        from academic.models import CourseEdition
        return CourseEdition.objects.filter(students=self.user).first()

    def update_course_info(self):
        """
        Update student_course_type and student_course_edition based on current enrollment.
        If not enrolled, sets course_type to "No inscrito" and course_edition to None.
        """
        from academic.models import CourseEdition
        # Get the most recent course enrollment
        current_course = CourseEdition.objects.filter(students=self.user).order_by('-start_date').first()
        
        if current_course:
            self.student_course_type = current_course.course_type.code
            self.student_course_edition = current_course.edition
        else:
            # Student is not enrolled in any course
            self.student_course_type = self.COURSE_NA
            self.student_course_edition = None

class InstructorProfile(models.Model):
    """Model for storing instructor-specific information and flight training credentials."""

    #region CHOICE DEFINITIONS

    # Instructor type
    GROUND = 'TIERRA'
    FLYING = 'VUELO'
    DUAL = 'DUAL'

    INSTRUCTOR_TYPES = [
        (GROUND, 'Escuela en tierra'),
        (FLYING, 'Línea de vuelo'),
        (DUAL, 'Dual'),
    ]

    # Instructor license
    LICENSE_NA = 'NA'
    LICENSE_PCA = 'PCA'
    LICENSE_TLA = 'TLA'
    LICENSE_IVS = 'IVS'
    LICENSE_OTHER = 'OTRO'

    LICENSE_TYPES = [
        (LICENSE_NA, 'N/A'),
        (LICENSE_PCA, 'PCA'),
        (LICENSE_TLA, 'TLA'),
        (LICENSE_IVS, 'IVS'),
        (LICENSE_OTHER, 'OTRO'),
    ]

    #endregion

    #region MODEL FIELDS

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')

    instructor_type = models.CharField(
        max_length=20, 
        choices=INSTRUCTOR_TYPES, 
        default=GROUND, 
        verbose_name='Tipo de Instructor',
    )

    instructor_license_type = models.CharField(
        max_length=10,
        choices=LICENSE_TYPES,
        default=LICENSE_PCA,
        verbose_name='Tipo de licencia',
    )

    #endregion

    class Meta:
        db_table = 'instructors_db'
        ordering = ['user__national_id']
        verbose_name = 'Instructor'
        verbose_name_plural = 'Instructores'

    def __str__(self):
        return f'{self.user.username} [ID: {self.user.national_id}] ({self.instructor_type})'


class StaffProfile(models.Model):
    """Model for storing staff member information and administrative roles."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')

    can_confirm_payments = models.BooleanField(default=False)

    class Meta:
        db_table = 'staff_db'
        ordering = ['user__national_id']
        verbose_name = 'Staff'
        verbose_name_plural = 'Staff'

    def __str__(self):
        return f'{self.user.username} [ID: {self.user.national_id}]'

class StudentPayment(models.Model):
    """Model for tracking student payments, balances, and payment confirmations."""

    student_profile = models.OneToOneField(
        'accounts.StudentProfile', 
        on_delete=models.CASCADE, 
        related_name='payment'
    )

    # Payment amount
    amount = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Date when the payment was made
    date_added = models.DateTimeField(auto_now_add=True)

    # The user who adds the payment (accounting manager)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )

    # Checks if the payment has been confirmed
    # by the director or authorized staff
    confirmed = models.BooleanField(default=False)
    
    # Admin who confirms the payment
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_student_payments',
        limit_choices_to={'staff_profile__can_confirm_payments': True}
    )

    # Date when the payment was confirmed
    confirmation_date = models.DateTimeField(null=True, blank=True)

    # Notes or comments about the payment
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'student_payments'
        ordering = ['-date_added', 'student_profile__user__national_id']
        verbose_name = 'Pago de Estudiante'
        verbose_name_plural = 'Pagos de Estudiantes'

    def __str__(self):
        return f"{self.student_profile.user.first_name} {self.student_profile.user.last_name} - ${self.amount}"

    def clean(self):
        """Validate payment data"""
        if self.amount <= 0:
            raise ValidationError('El monto debe ser mayor a cero')
        
        if self.confirmed and not self.confirmed_by:
            raise ValidationError('Un pago confirmado debe tener un usuario que lo confirme')
        
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
        if hasattr(self.student_profile, 'student_balance'):
            self.student_profile.student_balance += self.amount
            self.student_profile.save()
    
    def save(self, *args, **kwargs):
        """Override save method to validate data before saving"""
        # Automatically update confirmation_date if confirmed is set to True
        if self.confirmed and not self.confirmation_date:
            self.confirmation_date = timezone.now()
        super().save(*args, **kwargs)