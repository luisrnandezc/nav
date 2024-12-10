from django.db import models
from accounts.models import Student, Instructor
from django.core.validators import MinValueValidator, MaxValueValidator

class FlightLog(models.Model):
    """
    Flight Log Model

    This model receives data directly from the FlightEvaluation form.
    It generates records that allow students and authorized staff 
    to track and monitor students' flight training progress.
    """

    COURSE_TYPE_CHOICES = [
        ('pp', 'PP'),
        ('hvi', 'HVI'),
        ('pc', 'PC'),
        ('tla', 'TLA'),
    ]

    FLIGHT_RULES_CHOICES = [
        ('vfr', 'VFR'),
        ('ifr', 'IFR'),
        ('dual', 'Dual'),
    ]

    SESSION_GRADE_CHOICES = [
        ('s', 'Standard'),
        ('ns', 'Non-standard'),
    ]

    # TODO: this must be obtained from the FlightEvaluation form.
    student_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)]
    )

    # TODO: this must be obtained from the FlightEvaluation form.
    student_first_name = models.CharField(max_length=50)

    # TODO: this must be obtained from the FlightEvaluation form.
    student_last_name = models.CharField(max_length=50)

    # TODO: this must be obtained from the FlightEvaluation form.
    instructor_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)]
    )

    # TODO: this must be obtained from the FlightEvaluation form.
    instructor_first_name = models.CharField(max_length=50)

    # TODO: this must be obtained from the FlightEvaluation form.
    instructor_last_name = models.CharField(max_length=50)

    # TODO: this must be obtained from the FlightEvaluation form.
    hours_flown = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
    )

    # TODO: this must be obtained from the FlightEvaluation form.
    course_type = models.CharField(
        max_length=10, 
        choices=COURSE_TYPE_CHOICES,
    )

    # TODO: this must be obtained from the FlightEvaluation form.
    flight_rules = models.CharField(
        max_length=10, 
        choices=FLIGHT_RULES_CHOICES,
    )

    # TODO: this must be obtained from the FlightEvaluation form.
    solo_flight = models.BooleanField()

    # TODO: this must be obtained from the FlightEvaluation form.
    session_number = models.CharField()

    # TODO: this must be obtained from the FlightEvaluation form.
    session_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
    )

    # TODO: this is computed dynamically in the FlightEvaluation model.
    total_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
    )

    # TODO: this must be obtained from the FlightEvaluation form.
    aircraft_registration = models.CharField(max_length=6)

    # TODO: this must be obtained from the FlightEvaluation form.
    session_grade = models.CharField(
        max_length=2, 
        choices=SESSION_GRADE_CHOICES,
    )

    # TODO: this must be obtained from the FlightEvaluation form.
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Flight data: {self.flight_date} - {self.flight_hours} hrs'
    

class FlightEvaluation(models.Model):

    # TODO: check this infomation with NAV.
    INSTRUCTOR_LICENSE_TYPE_CHOICES = [
        ('type1', 'Tipo 1'),
        ('type2', 'Tipo 2'),
        ('type3', 'Tipo 3'),
    ]

    # TODO: check this infomation with NAV.
    STUDENT_LICENSE_TYPE_CHOICES = [
        ('type1', 'Tipo 1'),
        ('type2', 'Tipo 2'),
        ('type3', 'Tipo 3'),
    ]

    COURSE_TYPE_CHOICES = [
        ('pp', 'PP'),
        ('hvi', 'HVI'),
        ('pc', 'PC'),
        ('tla', 'TLA'),
    ]

    FLIGHT_RULES_CHOICES = [
        ('vfr', 'VFR'),
        ('ifr', 'IFR'),
        ('dual', 'Dual'),
    ]

    SESSION_GRADE_CHOICES = [
        ('s', 'S'),
        ('ns', 'NS'),
        ('ne', 'NE'),
    ]

    flight_date = models.DateTimeField(auto_now_add=True)

    # TODO: this could be extracted from current session. Maybe it must be added
    # first to the instructor registration form.
    instructor_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)]
    )

    instructor_first_name = models.CharField(max_length=50) # TODO: this could be extracted from current session. 

    instructor_last_name = models.CharField(max_length=50) # TODO: this could be extracted from current session.

    instructor_license_type = models.CharField(
        max_length=10,
        choices=INSTRUCTOR_LICENSE_TYPE_CHOICES,
    )

    # TODO: This field require some validation.
    instructor_license_number = models.PositiveIntegerField()

    student_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)]
    )

    student_first_name = models.CharField(max_length=50)

    student_last_name = models.CharField(max_length=50)

    # TODO: This field require some validation.
    student_license_number = models.PositiveIntegerField()

    course_type = models.CharField(
        max_length=10, 
        choices=COURSE_TYPE_CHOICES,
    )

    flight_rules = models.CharField(
        max_length=10, 
        choices=FLIGHT_RULES_CHOICES,
    )

    solo_flight = models.BooleanField()

    session_number = models.CharField()

    accumulated_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
    )

    session_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
    )

    aircraft_registration = models.CharField(max_length=6)

    session_grade = models.CharField(
        max_length=2, 
        choices=SESSION_GRADE_CHOICES,
    )

    notes = models.TextField(blank=True, null=True)

    def total_flight_hours(self):
        """Return the sum of accumulated and session flight hours."""
        return self.accumulated_flight_hours + self.session_flight_hours

    def __str__(self):
        return f'Flight data: {self.flight_date} - {self.flight_hours} hrs'

