from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Q
from accounts.models import Instructor, Student
import datetime

# General Course Type Model
class CourseType(models.Model):
    """Course model for all permanent courses (Private Pilot, Commercial Pilot, etc.)"""

    COURSE_CODES = (
        ('PPA', 'PPA'),
        ('HVI', 'HVI'),
        ('PCA', 'PCA'),
        ('TLA', 'TLA'),
        ('IVA', 'IVA'),
        ('IVS', 'IVS'),
        ('DDV', 'DDV'),
    )
    COURSE_NAMES = (
        ('Piloto Privado Avión', 'Piloto Privado Avión'),
        ('Habilitación Vuelo Instrumental Avión', 'Habilitación Vuelo Instrumental Avión'),
        ('Piloto Comercial Avión', 'Piloto Comercial Avión'),
        ('Transporte Línea Aérea Avión', 'Transporte Línea Aérea Avión'),
        ('Instructor de Vuelo Avión', 'Instructor de Vuelo Avión'),
        ('Instructor de Vuelo Simulado', 'Instructor de Vuelo Simulado'),
        ('Despachador de Vuelo', 'Despachador de Vuelo'),
    )

    code = models.CharField(max_length=10, unique=True, choices=COURSE_CODES, default='PPA')
    name = models.CharField(max_length=100, unique=True, choices=COURSE_NAMES, default='Piloto Privado')
    credit_hours = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Course Type'
        verbose_name_plural = 'Course Types'
    
    def __str__(self):
        return self.name

# Course Model (specific)
class CourseEdition(models.Model):
    """Course model for a specific course edition (Private Pilot 1, Commercial Pilot 5, etc.)"""
    course_type = models.ForeignKey(CourseType, on_delete=models.CASCADE, related_name='editions')
    edition = models.IntegerField(validators=[MinValueValidator(1)], default=1)
    start_date = models.DateField(default=datetime.date.today)
    students = models.ManyToManyField(Student, blank=True)

    TIME_SLOTS = (
        ('Mañana', 'Mañana'),
        ('Tarde', 'Tarde')
    )
    time_slot = models.CharField(max_length=10, choices=TIME_SLOTS)

    class Meta:
        verbose_name = 'Course Edition'
        verbose_name_plural = 'Course Editions'
        unique_together = ['course_type', 'edition']
    
    def __str__(self):
        return f"{self.course_type.name} - {self.edition}"
    
# Subject Model (Belongs to a Course Type)
class SubjectType(models.Model):
    """Subject type model for all permanent subjects (e.g., Aerodynamics I, Instruments II, etc.)"""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100, unique=True)
    course_type = models.ForeignKey(CourseType, on_delete=models.CASCADE, related_name='subjects')
    credit_hours = models.PositiveIntegerField(default=0)
    passing_grade = models.PositiveIntegerField(
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Nota mínima requerida para aprobar la materia"
    )

    class Meta:
        verbose_name = 'Subject Type'
        verbose_name_plural = 'Subject Types'

    def __str__(self):
        return f"{self.course_type.name} - {self.name}"

# Specific Subject Model (specific to a course)
class SubjectEdition(models.Model):
    """Specific edition of a subject"""
    subject_type = models.ForeignKey(SubjectType, on_delete=models.CASCADE, related_name='editions', null=True)
    
    instructor = models.ForeignKey(
        Instructor, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to=Q(instructor_type='TIERRA') | Q(instructor_type='DUAL')
    )
    students = models.ManyToManyField(
        Student,
        limit_choices_to={'student_phase': 'TIERRA'})

    TIME_SLOTS = (
        ('Mañana', 'Mañana'),
        ('Tarde', 'Tarde')
    )
    time_slot = models.CharField(max_length=10, choices=TIME_SLOTS)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(default=datetime.time(9, 0))
    end_time = models.TimeField(default=datetime.time(12, 30))

    class Meta:
        verbose_name = 'Subject Edition'
        verbose_name_plural = 'Subject Editions'

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError('La fecha de finalización debe ser posterior a la fecha de inicio')
        if self.end_time <= self.start_time:
            raise ValidationError('El horario de finalización debe ser posterior al horario de inicio')

    def __str__(self):
        subject = self.subject_type or self.base_subject
        return f"{subject.code} ({self.time_slot})"