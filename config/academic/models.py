from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
import datetime
from accounts.models import User

#region Choices

# Course Type Choices
COURSE_CODES = (
    ('PPA-T', 'PPA-T'),
    ('PPA-P', 'PPA-P'),
    ('HVI-T', 'HVI-T'),
    ('HVI-P', 'HVI-P'),
    ('PCA-T', 'PCA-T'),
    ('PCA-P', 'PCA-P'),
    ('IVA-T', 'IVA-T'),
    ('IVA-P', 'IVA-P'),
    ('IVS-T', 'IVS-T'),
    ('IVS-P', 'IVS-P'),
    ('RCL', 'RCL'),
)
COURSE_NAMES = (
    ('Piloto Privado Avión Teórico', 'Piloto Privado Avión Teórico'),
    ('Piloto Privado Avión Práctico', 'Piloto Privado Avión Práctico'),
    ('Habilitación Vuelo Instrumental Avión Teórico', 'Habilitación Vuelo Instrumental Avión Teórico'),
    ('Habilitación Vuelo Instrumental Avión Práctico', 'Habilitación Vuelo Instrumental Avión Práctico'),
    ('Piloto Comercial Avión Teórico', 'Piloto Comercial Avión Teórico'),
    ('Piloto Comercial Avión Práctico', 'Piloto Comercial Avión Práctico'),
    ('Instructor de Vuelo Avión Teórico', 'Instructor de Vuelo Avión Teórico'),
    ('Instructor de Vuelo Avión Práctico', 'Instructor de Vuelo Avión Práctico'),
    ('Instructor de Vuelo Simulado Teórico', 'Instructor de Vuelo Simulado Teórico'),
    ('Instructor de Vuelo Simulado Práctico', 'Instructor de Vuelo Simulado Práctico'),
    ('Recalificación', 'Recalificación'),
)

# Subject Choices by Course Type
SUBJECTS_CODES = (
    ('PPA-AER-I', 'PPA-AER-I'),
    ('PPA-SYE-I', 'PPA-SYE-I'),
    ('PPA-MET-I', 'PPA-MET-I'),
    ('PPA-DER-I', 'PPA-DER-I'),
    ('PPA-NAV', 'PPA-NAV'),
    ('PPA-UDM', 'PPA-UDM'),
    ('PPA-MYC', 'PPA-MYC'),
    ('PPA-PRF', 'PPA-PRF'),
    ('PPA-RDC', 'PPA-RDC'),
    ('PPA-FHH', 'PPA-FHH'),
    ('PPA-SEG', 'PPA-SEG'),
    ('PPA-SPV', 'PPA-SPV'),
    ('PPA-PRO-I', 'PPA-PRO-I'),
    ('HVI-DER', 'HVI-DER'),
    ('HVI-SYE', 'HVI-SYE'),
    ('HVI-PPV', 'HVI-PPV'),
    ('HVI-MET', 'HVI-MET'),
    ('HVI-RDN', 'HVI-RDN'),
    ('HVI-PRO', 'HVI-PRO'),
    ('HVI-CAR', 'HVI-CAR'),
    ('PCA-AER-II', 'PCA-AER-II'),
    ('PCA-SYE-II', 'PCA-SYE-II'),
    ('PCA-MET-II', 'PCA-MET-II'),
    ('PCA-DER-II', 'PCA-DER-II'),
    ('PCA-FHH-II', 'PCA-FHH-II'),
    ('PCA-INST-II', 'PCA-INST-II'),
    ('PCA-RDN', 'PCA-RDN'),
    ('PCA-PRO-II', 'PCA-PRO-II'),
    ('PCA-SEG-II', 'PCA-SEG-II'),
    ('IVA-PFD', 'IVA-PFD'),
    ('IVA-ADE', 'IVA-ADE'),
    ('IVS-PFD', 'IVS-PFD'),
    ('IVS-ADE', 'IVS-ADE'),
)

SUBJECTS_NAMES = (
    ('PPA-AER-I', 'PPA - Aeronáutica I'),
    ('PPA-SYE-I', 'PPA - Sistemas y Equipos I'),
    ('PPA-MET-I', 'PPA - Meteorología I'),
    ('PPA-DER-I', 'PPA - Derecho Aeronáutico I'),
    ('PPA-NAV', 'PPA - Navegación Visual'),
    ('PPA-UDM', 'PPA - Unidades de Medida'),
    ('PPA-MYC', 'PPA - Masa y Centrado'),
    ('PPA-PRF', 'PPA - Performance'),
    ('PPA-RDC', 'PPA - Radiocomunicaciones'),
    ('PPA-FHH', 'PPA - Factores Humanos'),
    ('PPA-SEG', 'PPA - Seguridad Aérea'),
    ('PPA-SPV', 'PPA - Supervivencia'),
    ('PPA-PRO-I', 'PPA - Procedimientos Operacionales I'),
    ('HVI-DER', 'HVI - Derecho Aeronáutico'),
    ('HVI-SYE', 'HVI - Sistemas y Equipos'),
    ('HVI-PPV', 'HVI - Performance y Planificación de Vuelo'),
    ('HVI-MET', 'HVI - Meteorología'),
    ('HVI-RDN', 'HVI - Radionavegación'),
    ('HVI-PRO', 'HVI - Procedimientos Operacionales'),
    ('HVI-CAR', 'HVI - Comunicaciones Aeronáuticas'),
    ('PCA-AER-II', 'PCA - Aerodinámica II'),
    ('PCA-SYE-II', 'PCA - Sistemas y Equipos II'),
    ('PCA-MET-II', 'PCA - Meteorología II'),
    ('PCA-DER-II', 'PCA - Derecho Aeronáutico II'),
    ('PCA-FHH-II', 'PCA - Factores Humanos II'),
    ('PCA-INST-II', 'PCA - Instrumentos II'),
    ('PCA-RDN', 'PCA - Radionavegación'),
    ('PCA-PRO-II', 'PCA - Procedimientos Operacionales II'),
    ('PCA-SEG-II', 'PCA - Seguridad Aérea II'),
    ('IVA-PFD', 'IVA - Peligros Durante la Simulación de Fallas'),
    ('IVA-ADE', 'IVA - Administración de la Enseñanza'),
    ('IVS-PFD', 'IVS - Peligros Durante la Simulación de Fallas'),
    ('IVS-ADE', 'IVS - Administración de la Enseñanza'),
)

# Time Slots
TIME_SLOTS = (
    ('M', 'Mañana'),
    ('T', 'Tarde'),
    ('N', 'Noche'),
)

# Test type choices
TEST_TYPES = (
    ('STANDARD', 'Estándar'),
    ('RECOVERY', 'Reparación'),
)

#endregion

#region Models
# General Course Type Model
class CourseType(models.Model):
    """Course model for all permanent courses (Private Pilot, Commercial Pilot, etc.)"""
    code = models.CharField(
        max_length=10, unique=True,
        choices=COURSE_CODES,
        default='PPA-T',
        verbose_name='Código'
    )
    name = models.CharField(
        max_length=100, 
        unique=True, 
        choices=COURSE_NAMES, 
        default='Piloto Privado Avión Teórico',
        verbose_name='Nombre'
    )
    credit_hours = models.PositiveIntegerField(
        default=0,
        verbose_name='Horas académicas'
    )
    
    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['code']
    
    def __str__(self):
        return self.name
    

# Course Model (specific)
class CourseEdition(models.Model):
    """Course model for a specific course edition (Private Pilot 1, Commercial Pilot 5, etc.)"""
    course_type = models.ForeignKey(
        CourseType, 
        on_delete=models.CASCADE, 
        related_name='editions',
        verbose_name='Tipo de Curso'
    )
    edition = models.IntegerField(
        validators=[MinValueValidator(0)], 
        default=0,
        verbose_name='Edición',
        blank=True,
        null=True,
    )
    students = models.ManyToManyField(
        User,
        limit_choices_to={'role': 'STUDENT'},
        related_name='enrolled_courses',
        blank=True
    )
    start_date = models.DateField(
        default=timezone.now,
        verbose_name='Fecha de inicio'
    )
    time_slot = models.CharField(
        max_length=10, 
        choices=TIME_SLOTS,
        verbose_name='Horario',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'Edición de Curso'
        verbose_name_plural = 'Ediciones de Cursos'
        unique_together = ['course_type', 'edition']
        ordering = ['course_type', 'edition']
    
    def __str__(self):
        return f"{self.course_type.name} - {self.edition}"
    
    
# Subject Model (Belongs to a Course Type)
class SubjectType(models.Model):
    """Subject type model for all permanent subjects (e.g., Aerodynamics I, Instruments II, etc.)"""
    course_type = models.ForeignKey(
        CourseType, 
        on_delete=models.CASCADE, 
        related_name='subjects',
        verbose_name='Tipo de Curso'
    )
    code = models.CharField(
        max_length=50, 
        unique=True, 
        choices=SUBJECTS_CODES,
        verbose_name='Código'
    )
    name = models.CharField(
        max_length=100, 
        unique=True, 
        choices=SUBJECTS_NAMES,
        verbose_name='Nombre'
    )
    credit_hours = models.PositiveIntegerField(
        default=0,
        verbose_name='Horas académicas'
    )
    passing_grade = models.PositiveIntegerField(
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Nota mínima requerida para aprobar'
    )
    recovery_passing_grade = models.PositiveIntegerField(
        default=90,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Nota mínima requerida para aprobar la reparación'
    )

    class Meta:
        verbose_name = 'Materia'
        verbose_name_plural = 'Materias'
        ordering = ['course_type', 'code']

    def __str__(self):
        return f"{self.name} ({self.code})"
    

# Specific Subject Model (specific to a course)
class SubjectEdition(models.Model):
    """Specific edition of a subject"""
    subject_type = models.ForeignKey(
        SubjectType, 
        on_delete=models.CASCADE, 
        related_name='editions',
        verbose_name='Tipo de Materia',
        null=True
    )
    instructor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to=Q(instructor_profile__instructor_type='TIERRA') | Q(instructor_profile__instructor_type='DUAL'),
        related_name='teaching_subjects',
        verbose_name='Instructor'
    )
    students = models.ManyToManyField(
        User,
        limit_choices_to={'role': 'STUDENT'},
        related_name='enrolled_subjects',
        blank=True,
        verbose_name='Estudiantes'
    )
    time_slot = models.CharField(
        max_length=10, 
        choices=TIME_SLOTS,
        verbose_name='Horario'
    )
    start_date = models.DateField(
        default=timezone.now,
        verbose_name='Fecha de inicio'
    )
    end_date = models.DateField(
        default=timezone.now,
        verbose_name='Fecha de finalización'
    )
    start_time = models.TimeField(
        default=datetime.time(9, 0),
        verbose_name='Hora de inicio'
    )
    end_time = models.TimeField(
        default=datetime.time(12, 30),
        verbose_name='Hora de finalización'
    )

    class Meta:
        verbose_name = 'Edición de Materia'
        verbose_name_plural = 'Ediciones de Materias'
        ordering = ['subject_type']

    def clean(self):
        if not self.subject_type:
            raise ValidationError('Debe seleccionar un tipo de materia')
            
        if self.end_date < self.start_date:
            raise ValidationError('La fecha de finalización debe ser posterior a la fecha de inicio')
        
        if self.end_time <= self.start_time:
            raise ValidationError('La hora de finalización debe ser posterior a la hora de inicio')
        
        # Check if instructor is assigned
        if not self.instructor:
            raise ValidationError('Debe asignar un instructor a la materia')
        
        # Check if instructor is qualified for this subject type
        if self.instructor and self.subject_type:
            instructor_type = self.instructor.instructor_profile.instructor_type
            if instructor_type not in ['TIERRA', 'DUAL']:
                raise ValidationError('El instructor debe ser de tipo TIERRA o DUAL')

    def __str__(self):
        return f'{self.subject_type.code} ({self.time_slot})'


class StudentGrade(models.Model):
    """Model for storing student grades in ground school subjects"""

    #region RELATIONSHIPS
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'STUDENT'},
        related_name='grades',
        verbose_name='Estudiante',
        null=False,
        blank=False,
    )
    instructor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to=Q(instructor_profile__instructor_type='TIERRA') | Q(instructor_profile__instructor_type='DUAL'),
        related_name='submitted_grades',
        verbose_name='Instructor',
        null=False,
        blank=False,
    )
    subject_edition = models.ForeignKey(
        SubjectEdition,
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name='Edición de Materia'
    )
    #endregion

    #region GRADE DATA
    grade = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Nota'
    )
    test_type = models.CharField(
        max_length=10,
        choices=TEST_TYPES,
        default='STANDARD',
        verbose_name='Tipo de Examen'
    )
    date = models.DateField(
        auto_now_add=True,
        verbose_name='Fecha'
    )
    #endregion

    class Meta:
        verbose_name = 'Nota de Estudiante'
        verbose_name_plural = 'Notas de Estudiantes'
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=["subject_edition", "student", "test_type"],
                name="unique_student_grade",
                violation_error_message="Ya existe una nota para este estudiante con el mismo tipo de examen"
            ),
        ]

    def __str__(self):
        return f'{self.student.first_name} {self.student.last_name} - {self.subject_edition.subject_type.name} ({self.grade})'

    @property
    def passed(self):
        """Check if the student passed the exam based on test type and passing grade"""
        passing_grade = (
            self.subject_edition.subject_type.recovery_passing_grade
            if self.test_type == 'RECOVERY'
            else self.subject_edition.subject_type.passing_grade
        )
        return self.grade >= passing_grade
#endregion