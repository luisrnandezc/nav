from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from constants import COURSE_NA

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
    
    username = models.CharField(
        max_length=150, 
        unique=True, 
        verbose_name='Usuario'
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Email',
    )
    first_name = models.CharField(
        max_length=150, 
        verbose_name='Nombre'
    )    
    last_name = models.CharField(
        max_length=150, 
        verbose_name='Apellido'
    )
    national_id = models.IntegerField(
        validators=[MinValueValidator(999999), MaxValueValidator(100000000)],
        unique=True, 
        verbose_name='Cédula',
    )
    role = models.CharField(
        max_length=10, 
        choices=Role.choices, 
        verbose_name='Rol'
    )

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

    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='student_profile'
    )
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
    sim_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(0)],
        verbose_name='Horas sim',
        default=0,
    )
    flight_hours = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[MinValueValidator(0)],
        verbose_name='Horas de vuelo',
        default=0,
    )
    nav_flight_hours = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[MinValueValidator(0)],
        verbose_name='Horas NAV',
        default=0,
    )
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Balance',
        default=0.00,
    )
    flight_rate = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        default=130.0,
        verbose_name="Tasa de vuelo ($/h)"
    )
    advanced_student = models.BooleanField(
        verbose_name='Estudiante avanzado',
        default=False,
    )
    has_credit = models.BooleanField(
        verbose_name='Tiene crédito',
        default=False,
        help_text='Permiso permanente para solicitar vuelos sin restricciones de balance.',
    )
    has_temp_permission = models.BooleanField(
        verbose_name='Tiene permiso temporal',
        default=False,
        help_text='Permiso temporal para solicitar vuelos sin restricciones de balance. Debe ser reactivado antes de cada vuelo.',
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
        return current_course.course_type.code if current_course else COURSE_NA

    @property
    def current_course_edition(self):
        """Get the current course edition number or None if not enrolled."""
        from academic.models import CourseEdition
        current_course = CourseEdition.objects.filter(students=self.user).order_by('-start_date').first()
        return current_course.edition if current_course else None
    
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
        # Get the most recent course enrollment
        from academic.models import CourseEdition
        current_course = CourseEdition.objects.filter(students=self.user).order_by('-start_date').first()
        
        if current_course:
            self.student_course_type = current_course.course_type.code
            self.student_course_edition = current_course.edition
        else:
            # Student is not enrolled in any course
            self.student_course_type = COURSE_NA
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

    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='instructor_profile'
    )
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
    instructor_hourly_rate = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=20.0,
        verbose_name="Tasa de instrucción ($/h)"
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

    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='staff_profile'
    )
    position = models.CharField(
        max_length=100,
        default='Staff',
        verbose_name='Cargo',
    )

    class Meta:
        db_table = 'staff_db'
        ordering = ['user__national_id']
        verbose_name = 'Staff'
        verbose_name_plural = 'Staff'
        permissions = [
            ('can_confirm_transactions', 'Can confirm transactions'),
            ('can_manage_transactions', 'Can manage transactions'),
            ('can_manage_sms', 'Can manage SMS'),
        ]

    def __str__(self):
        return f'{self.user.username} [ID: {self.user.national_id}] ({self.position})'