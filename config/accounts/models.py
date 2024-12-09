from django.db import models
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


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
        primary_key=True,
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

    balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name='Balance para Línea de Vuelo'
    )

    class Meta:
        db_table = 'students_db'
        ordering = ['student_id']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return f'{self.user.username} [ID: {self.student_id}] ({self.student_type} - {self.student_course_type})'
    
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
        if self.student_type == self.GROUND and self.balance != 0:
            raise ValidationError({
                'balance': 'Balance must be zero for ground students.'
            })
    
    def save(self, *args, **kwargs):
        """
        Override the save method to ensure the balance is reset to 0
        when the student type is changed from 'flying' to 'ground'.
        """
        if self.student_type == self.GROUND:
            self.balance = 0.00
        super().save(*args, **kwargs)
        

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
        primary_key=True,
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
    

class Staff(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    staff_id = models.PositiveBigIntegerField(
        verbose_name='Identificación',
        unique=True,
        primary_key=True,
        validators=[MinValueValidator(1)],
        help_text='Número de cédula o pasaporte sin puntos o guiones.'
    )

    class Meta:
        db_table = 'staff_db'
        ordering = ['staff_id']
        verbose_name = 'Staff'
        verbose_name_plural = 'Staff'

    
    def __str__(self):
        return f'{self.user.username} [ID: {self.staff_id}])'
    

class FlightLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, to_field='student_id')
    flight_date = models.DateTimeField(auto_now_add=True)
    flight_hours = models.DecimalField(max_digits=5, decimal_places=2)

    instructor = models.CharField(max_length=100)

    def __str__(self):
        return f'Flight on {self.flight_date} - {self.flight_hours} hrs'
    