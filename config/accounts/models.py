from django.db import models
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse


class Student(models.Model):

    # Student Types
    GROUND = 'ground'
    FLYING = 'flying'

    STUDENT_TYPES = [
        (GROUND, 'Tierra'),
        (FLYING, 'Vuelo')
    ]

    # Course Types
    COURSE_PP = 'pp'
    COURSE_HVI = 'hvi'
    COURSE_PC = 'pc'
    COURSE_TLA = 'tla'

    COURSE_TYPES = [
        (COURSE_PP, 'PP'),
        (COURSE_HVI, 'HVI'),
        (COURSE_PC, 'PC'),
        (COURSE_TLA, 'TLA')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    student_id = models.PositiveBigIntegerField(
        verbose_name='Identificación',
        unique=True,
        validators=[MinValueValidator(1)],
        help_text='Número de cédula o pasaporte sin puntos o guiones.'
    )

    student_type = models.CharField(
        max_length=6, 
        choices=STUDENT_TYPES, 
        default='ground', 
        verbose_name='Tipo de Estudiante'
    )
    
    student_age = models.PositiveIntegerField(
        validators=[MinValueValidator(16), MaxValueValidator(100)], 
        verbose_name='Edad'
    )
    
    student_course_type = models.CharField(
        max_length=3, 
        choices=COURSE_TYPES, 
        default='pp', 
        verbose_name='Curso'
    )
    
    student_course_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], 
        verbose_name='Número de Curso'
    )

    class Meta:
        db_table = 'students_db'
        ordering = ['student_id']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    
    def __str__(self):
        return f'{self.user.username} [ID: {self.student_id}] ({self.student_type} - {self.student_course_type})'
    


class Instructor(models.Model):

    # Instructor Types
    GROUND = 'ground'
    FLYING = 'flying'

    INSTRUCTOR_TYPES = [
        (GROUND, 'Tierra'),
        (FLYING, 'Vuelo')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    instructor_id = models.PositiveBigIntegerField(
        verbose_name='Identificación',
        unique=True,
        validators=[MinValueValidator(1)],
        help_text='Número de cédula o pasaporte sin puntos o guiones.'
    )

    instructor_type = models.CharField(
        max_length=6, 
        choices=INSTRUCTOR_TYPES, 
        default='ground', 
        verbose_name='Tipo de Instructor'
    )

    class Meta:
        db_table = 'instructors_db'
        ordering = ['instructor_id']
        verbose_name = 'Instructor'
        verbose_name_plural = 'Instructors'

    
    def __str__(self):
        return f'{self.user.username} [ID: {self.instructor_id}] ({self.instructor_type})'
