from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
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
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

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

    def clean(self):
        """
        Custom validation for the 'balance' field.
        If the student is not a 'flying' student, the balance must be zero.
        """
        if self.student_phase == self.GROUND and self.student_balance != 0:
            raise ValidationError({
                'student_balance': 'Balance must be zero for ground students.'
            })
    
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

    def save(self, *args, **kwargs):
        """
        Override the save method to ensure the balance is reset to 0
        when the student type is changed from 'flying' to 'ground'.
        Also update course information based on current enrollment.
        """
        if self.student_phase == self.GROUND:
            self.student_balance = 0.00
        self.update_course_info()
        super().save(*args, **kwargs)


class InstructorProfile(models.Model):

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
        verbose_name_plural = 'Instructors'

    
    def __str__(self):
        return f'{self.user.username} [ID: {self.user.national_id}] ({self.instructor_type})'


class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')

    class Meta:
        db_table = 'staff_db'
        ordering = ['user__national_id']
        verbose_name = 'Staff'
        verbose_name_plural = 'Staff'

    def __str__(self):
        return f'{self.user.username} [ID: {self.user.national_id}]'