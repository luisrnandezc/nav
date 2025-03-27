from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from accounts.models import Instructor, Student
import datetime

# Base Course Model (general)
class BaseCourse(models.Model):
    """Base course model for all permanent courses (Private Pilot, Commercial Pilot, etc.)"""
    code = models.CharField(max_length=10, unique=True) # Example: "PPA"
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

# Course Edition Model (specific)
class CourseEdition(models.Model):
    """Course edition model for a specific course (Private Pilot 1, Commercial Pilot 5, etc.)"""
    base_course = models.ForeignKey(BaseCourse, on_delete=models.CASCADE, related_name='editions')
    edition = models.IntegerField(validators=[MinValueValidator(1)])
    start_date = models.DateField()
    students = models.ManyToManyField(Student, blank=True)

    TIME_SLOTS = (
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon')
    )
    time_slot = models.CharField(max_length=10, choices=TIME_SLOTS)

    def __str__(self):
        return f"{self.base_course.name} - {self.edition}"
    
# Subject Model (Belongs to a Course)
class BaseSubject(models.Model):
    """Base subject model for all permanent subjects (e.g., Aerodynamics I, Instruments II, etc.)"""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100, unique=True)
    base_course = models.ForeignKey(BaseCourse, on_delete=models.CASCADE, related_name='base_subjects')
    credit_hours = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.base_course.name} - {self.name}"

# Subject Instance Model (specific)
class SubjectInstance(models.Model):
    """Specific instance of a subject"""
    base_subject = models.ForeignKey(BaseSubject, on_delete=models.CASCADE, related_name='subject_instances')
    instructor = models.ForeignKey(
        Instructor, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to={'instructor_type': ['TIERRA', 'DUAL']}
    )
    students = models.ManyToManyField(
        Student, 
        limit_choices_to={'student_phase': 'TIERRA'})

    TIME_SLOTS = (
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon')
    )
    time_slot = models.CharField(max_length=10, choices=TIME_SLOTS)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(default=datetime.time(9, 0))
    end_time = models.TimeField(default=datetime.time(12, 30))

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError('La fecha de finalización debe ser posterior a la fecha de inicio')
        if self.end_time <= self.start_time:
            raise ValidationError('El horario de finalización debe ser posterior al horario de inicio')

    def __str__(self):
        return f"{self.base_subject.code} ({self.time_slot})"