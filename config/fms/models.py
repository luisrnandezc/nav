from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class FlightLog(models.Model):
    """
    Flight Log Model

    This model receives data directly from the FlightEvaluation form.
    It generates records that allow students and authorized staff 
    to track and monitor students' flight training progress.
    """

    #region CHOICES DEFINITIONS

    # Course types
    COURSE_PP = 'PP'
    COURSE_HVI = 'HVI'
    COURSE_PC = 'PC'
    COURSE_TLA = 'TLA'

    COURSE_TYPE_CHOICES = [
        (COURSE_PP, 'PP'),
        (COURSE_HVI, 'HVI'),
        (COURSE_PC, 'PC'),
        (COURSE_TLA, 'TLA'),
    ]

    # Flight rules
    VFR = 'VFR'
    IFR = 'IFR'
    DUAL = 'DUAL'

    FLIGHT_RULES_CHOICES = [
        (VFR, 'VFR'),
        (IFR, 'IFR'),
        (DUAL, 'Dual'),
    ]

    # Solo flight
    NO = 'N'
    YES = 'Y'

    SOLO_FLIGHT_CHOICES = [
        (NO, 'N'),
        (YES, 'Y'),
    ]

    # Session number
    def generate_choices():
        choices = []
        for i in range(1, 21):
            choices.append((str(i), str(i)))
        return choices
    
    # Session letter
    SESSION_LETTER_CHOICES = [
        ('', ''),
        ('A', 'A'),
        ('B', 'B'),
        ('E', 'E'),
    ]

    # Flight session grades
    STANDARD = 'S'
    NON_STANDARD = 'NS'
    NOT_EVALUATED = 'NE'

    SESSION_GRADE_CHOICES = [
        (STANDARD, 'S'),
        (NON_STANDARD, 'NS'),
        (NOT_EVALUATED, 'NE'),
    ]

    # Aircraft registration
    YV1111 = 'YV1111'
    YV2222 = 'YV2222'

    AIRCRAFT_REG = [
        (YV1111, 'YV1111'),
        (YV2222, 'YV2222'),
    ]

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
    course_type = models.CharField(
        max_length=3, 
        choices=COURSE_TYPE_CHOICES,
        default=COURSE_PP,
    )
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
    #endregion

    #region SESSION DATA
    flight_date = models.DateTimeField(
        auto_now_add=True
    )
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
        choices=generate_choices(),
        default='1',
    )
    session_letter = models.CharField(
        max_length=1,
        choices=SESSION_LETTER_CHOICES,
        blank=True,
        null=True,
        default='',
    )
    accumulated_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=0.00,
    )
    session_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=0.00,
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
    notes = models.TextField(
        blank=False
    )
    #endregion

    def __str__(self):
        return f'Flight data: {self.flight_date} - {self.flight_hours} hrs'
    

class FlightEvaluation(models.Model):
    """
    Flight Evaluation Model

    This model receives data directly from the FlightEvaluation form.
    It generates flight session records that are used to generate pdf
    files and serve as a digital backup of flight training sessions.
    """

    #region CHOICES DEFINITIONS

    # License types
    LICENSE_AP = 'AP'
    LICENSE_PP = 'PP'
    LICENSE_PC = 'PC'
    LICENSE_TLA = 'TLA'

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
    COURSE_PP = 'PP'
    COURSE_HVI = 'HVI'
    COURSE_PC = 'PC'
    COURSE_TLA = 'TLA'

    COURSE_TYPE_CHOICES = [
        (COURSE_PP, 'PP'),
        (COURSE_HVI, 'HVI'),
        (COURSE_PC, 'PC'),
        (COURSE_TLA, 'TLA'),
    ]

    # Flight rules
    VFR = 'VFR'
    IFR = 'IFR'
    DUAL = 'DUAL'

    FLIGHT_RULES_CHOICES = [
        (VFR, 'VFR'),
        (IFR, 'IFR'),
        (DUAL, 'Dual'),
    ]

    # Solo flight
    NO = 'N'
    YES = 'Y'
 
    SOLO_FLIGHT_CHOICES = [
        (NO, 'N'),
        (YES, 'Y'),
    ]

    # Flight session grades
    STANDARD = 'S'
    NON_STANDARD = 'NS'
    NOT_EVALUATED = 'NE'

    SESSION_GRADE_CHOICES = [
        (STANDARD, 'S'),
        (NON_STANDARD, 'NS'),
        (NOT_EVALUATED, 'NE'),
    ]

    # Session number
    def generate_choices():
        choices = []
        for i in range(1, 21):
            choices.append((str(i), str(i)))
        return choices
    
    # Session letter
    SESSION_LETTER_CHOICES = [
        ('', ''),
        ('A', 'A'),
        ('B', 'B'),
        ('E', 'E'),
    ]

    # Aircraft registration
    YV1111 = 'YV1111'
    YV2222 = 'YV2222'

    AIRCRAFT_REG = [
        (YV1111, 'YV1111'),
        (YV2222, 'YV2222'),
    ]

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
        max_length=3, 
        choices=COURSE_TYPE_CHOICES,
        default=COURSE_PP,
    )
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

    #region SESSION DATA
    flight_date = models.DateTimeField(
        auto_now_add=True
    )
    flight_rules = models.CharField(
        max_length=4, 
        choices=FLIGHT_RULES_CHOICES,
        default=VFR,
    )
    solo_flight = models.CharField(
        max_length=3,
        choices=SOLO_FLIGHT_CHOICES,
        default=NO,
    )
    session_number = models.CharField(
        max_length=3,
        choices=generate_choices(),
        default='1',
    )
    session_letter = models.CharField(
        max_length=1,
        choices=SESSION_LETTER_CHOICES,
        blank=True,
        null=True,
        default='',
    )
    accumulated_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=0.00,
    )
    session_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=0.00,
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

    #region PRE-FLIGHT
    pre_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    pre_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    pre_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    pre_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    pre_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    #endregion

    #region TAKEOFF
    to_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    to_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    to_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    to_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    to_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    to_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    #endregion

    #region MANEUVERS
    mvrs_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    mvrs_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    mvrs_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    mvrs_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    mvrs_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    mvrs_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    mvrs_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    mvrs_8 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    mvrs_9 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    mvrs_10 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    mvrs_11 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    mvrs_12 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    mvrs_13 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    mvrs_14 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    mvrs_15 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    mvrs_16 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    mvrs_17 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    #endregion

    #region EMERGENCIES
    emer_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    emer_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    emer_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    emer_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    emer_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    #endregion

    #region NAVIGATION VFR/IFR
    nav_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    nav_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    nav_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    nav_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    nav_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    nav_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    nav_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    nav_8 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    nav_9 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    #endregion

    #region GENERAL
    gen_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    gen_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    gen_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    gen_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    gen_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    gen_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    gen_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    #endregion

    #region INSTRUMENT FLIGHT
    inst_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    inst_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    inst_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    inst_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    inst_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    inst_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    inst_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    inst_8 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    inst_9 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    inst_10 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    inst_11 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    inst_12 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    #endregion

    #region LANDING
    land_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    land_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    land_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    land_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    land_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    land_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    land_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    land_8 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    land_9 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    land_10 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    land_11 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    land_12 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    land_13 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    land_14 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    land_15 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
    )
    #endregion

    notes = models.TextField(blank=False)

    def total_flight_hours(self):
        """Return the sum of accumulated and session flight hours."""
        return self.accumulated_flight_hours + self.session_flight_hours

    def __str__(self):
        return f'Flight data: {self.flight_date} - {self.flight_hours} hrs'

    #endregion