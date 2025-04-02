from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Student(models.Model):

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
    COURSE_PPA = 'PPA'
    COURSE_HVI = 'HVI'
    COURSE_PCA = 'PCA'
    COURSE_IVA = 'IVA'
    COURSE_IVS = 'IVS'
    COURSE_DDV = 'DDV'
    COURSE_NA = 'N/A'

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

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    student_id = models.PositiveIntegerField(
        verbose_name='Identificación',
        unique=True,
        primary_key=True,
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        help_text='Número de cédula o pasaporte sin puntos o guiones.',
    )

    student_age = models.PositiveIntegerField(
        validators=[MinValueValidator(16), MaxValueValidator(100)], 
        verbose_name='Edad',
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
    
    student_course_type = models.CharField(
        max_length=3, 
        choices=COURSE_TYPES, 
        default=COURSE_NA, 
        verbose_name='Curso',
    )
    
    student_course_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], 
        verbose_name='Número de Curso',
    )

    student_license_type = models.CharField(
        max_length=3,
        choices=LICENSE_TYPES,
        default=LICENSE_AP,
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
        ordering = ['student_id']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return f'{self.user.username} [ID: {self.student_id}] ({self.student_phase} - {self.student_course_type})'
    
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
        return CourseEdition.objects.filter(students=self).first()

    def update_course_info(self):
        """
        Update student_course_type and student_course_number based on current enrollment.
        If not enrolled, sets course_type to "No inscrito" and course_number to 0.
        """
        current_course = self.get_current_course()
        if current_course:
            self.student_course_type = current_course.course_type.code
            self.student_course_number = current_course.edition
        else:
            self.student_course_type = 'N/A'  # No inscrito
            self.student_course_number = 0

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
        

class Instructor(models.Model):

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

    LICENSE_TYPES = [
        (LICENSE_NA, 'N/A'),
        (LICENSE_PCA, 'PCA'),
        (LICENSE_TLA, 'TLA'),
    ]

    #endregion

    #region MODEL FIELDS

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    instructor_id = models.PositiveIntegerField(
        verbose_name='Identificación',
        unique=True,
        primary_key=True,
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        help_text='Número de cédula o pasaporte sin puntos o guiones.',
    )

    instructor_type = models.CharField(
        max_length=20, 
        choices=INSTRUCTOR_TYPES, 
        default=GROUND, 
        verbose_name='Tipo de Instructor',
    )

    instructor_license_type = models.CharField(
        max_length=3,
        choices=LICENSE_TYPES,
        default=LICENSE_PCA,
        verbose_name='Tipo de licencia',
    )

    #endregion

    class Meta:
        db_table = 'instructors_db'
        ordering = ['instructor_id']
        verbose_name = 'Instructor'
        verbose_name_plural = 'Instructors'

    
    def __str__(self):
        return f'{self.user.username} [ID: {self.instructor_id}] ({self.instructor_type})'
    

class Staff(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    staff_id = models.PositiveIntegerField(
        verbose_name='Identificación',
        unique=True,
        primary_key=True,
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        help_text='Número de cédula o pasaporte sin puntos o guiones.',
    )

    class Meta:
        db_table = 'staff_db'
        ordering = ['staff_id']
        verbose_name = 'Staff'
        verbose_name_plural = 'Staff',

    
    def __str__(self):
        return f'{self.user.username} [ID: {self.staff_id}])'