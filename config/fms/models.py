from django.db import models
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
    student_first_name = models.CharField(
        max_length=50,
        default='none',
    )

    # TODO: this must be obtained from the FlightEvaluation form.
    student_last_name = models.CharField(
        max_length=50,
        default='none',
    )

    # TODO: this must be obtained from the FlightEvaluation form.
    instructor_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)]
    )

    # TODO: this must be obtained from the FlightEvaluation form.
    instructor_first_name = models.CharField(
        max_length=50,
        default='none',
    )

    # TODO: this must be obtained from the FlightEvaluation form.
    instructor_last_name = models.CharField(
        max_length=50,
        default='none',
    )

    # TODO: this must be obtained from the FlightEvaluation form.
    course_type = models.CharField(
        max_length=10, 
        choices=COURSE_TYPE_CHOICES,
        default='none',
    )

    # TODO: this must be obtained from the FlightEvaluation form.
    flight_rules = models.CharField(
        max_length=10, 
        choices=FLIGHT_RULES_CHOICES,
        default='none',
    )

    # TODO: this must be obtained from the FlightEvaluation form.
    solo_flight = models.BooleanField()

    # TODO: this must be obtained from the FlightEvaluation form.
    session_number = models.CharField(
        max_length=5,
        default='none',
    )

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
    aircraft_registration = models.CharField(
        max_length=6,
        default='none',
    )

    # TODO: this must be obtained from the FlightEvaluation form.
    session_grade = models.CharField(
        max_length=2, 
        choices=SESSION_GRADE_CHOICES,
        default='none',
    )

    # TODO: this must be obtained from the FlightEvaluation form.
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Flight data: {self.flight_date} - {self.flight_hours} hrs'
    

class FlightEvaluation(models.Model):
    """
    Flight Evaluation Model

    This model receives data directly from the FlightEvaluation form.
    It generates flight session records that are used to generate pdf
    files and serve as a digital backup of flight training sessions.

    # TODO: add remaining flight training test parameters.
    """

    #region CHOICES DEFINITIONS

    # License types
    LICENSE_AP = 'ap'
    LICENSE_PP = 'pp'
    LICENSE_PC = 'pc'
    LICENSE_TLA = 'tla'

    INSTRUCTOR_LICENSE_CHOICES = [ 
        (LICENSE_PC, 'PC'),
        (LICENSE_TLA, 'TLA'),
    ]

    STUDENT_LICENSE_CHOICES = [
        (LICENSE_AP, 'AP'),
        (LICENSE_PP, 'PP'),
        (LICENSE_PC, 'PC'),
        (LICENSE_TLA, 'TLA'),
    ]

    # Course types
    COURSE_PP = 'pp'
    COURSE_HVI = 'hvi'
    COURSE_PC = 'pc'
    COURSE_TLA = 'tla'

    COURSE_TYPE_CHOICES = [
        (COURSE_PP, 'PP'),
        (COURSE_HVI, 'HVI'),
        (COURSE_PC, 'PC'),
        (COURSE_TLA, 'TLA'),
    ]

    # Flight rules
    VFR = 'vfr'
    IFR = 'ifr'
    DUAL = 'dual'

    FLIGHT_RULES_CHOICES = [
        (VFR, 'VFR'),
        (IFR, 'IFR'),
        (DUAL, 'Dual'),
    ]

    # Solo flight
    YES = 'y'
    NO = 'n'

    SOLO_FLIGHT_CHOICES = [
        (YES, 'Y'),
        (NO, 'N'),
    ]

    # Flight session grades
    STANDARD = 's'
    NON_STANDARD = 'ns'
    NOT_EVALUATED = 'ne'

    SESSION_GRADE_CHOICES = [
        (STANDARD, 'S'),
        (NON_STANDARD, 'NS'),
        (NOT_EVALUATED, 'NE'),
    ]

    # Session number
    def generate_choices():
        choices = []
        for i in range(1, 21):
            choices.append((i, i))
        return choices
    
    # Session letter
    SESSION_LETTER_CHOICES = [
        ('', ''),
        ('a', 'A'),
        ('b', 'B'),
        ('e', 'E'),
    ]

    # Aircraft registration
    YV1111 = 'yv1111'
    YV2222 = 'yv2222'

    AIRCRAFT_REG = [
        (YV1111, 'YV1111'),
        (YV2222, 'YV2222'),
    ]

    #endregion

    #region INSTRUCTOR DATA

    instructor_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)]
    )

    instructor_first_name = models.CharField(
        max_length=50,
        default='',
    )

    instructor_last_name = models.CharField(
        max_length=50,
        default='',
    )

    instructor_license_type = models.CharField(
        max_length=3,
        choices=INSTRUCTOR_LICENSE_CHOICES,
        default=LICENSE_PC,
    )

    instructor_license_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)]
    )
    
    #endregion

    #region STUDENT DATA

    student_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)]
    )

    student_first_name = models.CharField(
        max_length=50,
        default='',
    )

    student_last_name = models.CharField(
        max_length=50,
        default='',
    )

    student_license_type = models.CharField(
        max_length=3,
        choices=STUDENT_LICENSE_CHOICES,
        default=LICENSE_AP,
    )

    student_license_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)]
    )

    course_type = models.CharField(
        max_length=10, 
        choices=COURSE_TYPE_CHOICES,
        default=COURSE_PP,
    )

    #endregion

    #region FLIGHT INFORMATION

    flight_date = models.DateTimeField(auto_now_add=True)

    flight_rules = models.CharField(
        max_length=4, 
        choices=FLIGHT_RULES_CHOICES,
        default=VFR,
    )

    solo_flight = models.CharField(
        max_length=3,
        choices=SOLO_FLIGHT_CHOICES,
        default=YES,
    )

    session_number = models.CharField(
        max_length=3,
        choices=generate_choices,
        default='1',
    )

    session_letter = models.CharField(
        max_length=1,
        choices=SESSION_LETTER_CHOICES,
        default='',
    )

    accumulated_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
    )

    session_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
    )

    aircraft_registration = models.CharField(
        max_length=6,
        choices=AIRCRAFT_REG,
        default=YV1111,
    )

    session_grade = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )

    #endregion

    notes = models.TextField(blank=True, null=True)

    def total_flight_hours(self):
        """Return the sum of accumulated and session flight hours."""
        return self.accumulated_flight_hours + self.session_flight_hours

    def __str__(self):
        return f'Flight data: {self.flight_date} - {self.flight_hours} hrs'

