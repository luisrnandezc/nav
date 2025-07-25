from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator, MaxLengthValidator
from accounts.models import StudentProfile
from django.utils import timezone

class SimulatorLog(models.Model):
    """
    Simulator Log Model

    This model receives data directly from the FlightEvaluationSim form.
    It generates records that allow students and authorized staff 
    to track and monitor students' simulator training progress.
    """

    #region CHOICES DEFINITIONS

    # Course types
    COURSE_TYPE_CHOICES = StudentProfile.COURSE_TYPES

    # Flight rules
    VFR = 'VFR'
    IFR = 'IFR'
    DUAL = 'DUAL'

    FLIGHT_RULES_CHOICES = [
        (VFR, 'VFR'),
        (IFR, 'IFR'),
        (DUAL, 'Dual'),
    ]

    # Pre-solo flight
    NO = 'NO'
    YES = 'SI'

    PRE_SOLO_FLIGHT_CHOICES = [
        (NO, 'NO'),
        (YES, 'SI'),
    ]

    # Session number
    def generate_choices():
        choices = []
        for i in range(1, 11):
            choices.append((str(i), str(i)))
        return choices
    
    # Session letter
    SESSION_LETTER_CHOICES = [
        ('', ''),
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
    ]

    # Flight session grades
    SUPER_STANDARD = 'SS'
    STANDARD = 'S'
    NON_STANDARD = 'NS'
    NOT_EVALUATED = 'NE'

    SESSION_GRADE_CHOICES = [
        (SUPER_STANDARD, 'SS'),
        (STANDARD, 'S'),
        (NON_STANDARD, 'NS'),
        (NOT_EVALUATED, 'NE'),
    ]

    # Simulator
    FPT = 'FPT'
    B737 = 'B737'

    SIMULATOR_CHOICES = [
        (FPT, 'FPT'),
        (B737, 'B737'),
    ]
    #endregion

    evaluation_id = models.PositiveIntegerField(
        verbose_name='ID',
        help_text='ID única de evaluación asociada',
    )

    #region STUDENT DATA
    student_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='ID alumno'
    )
    student_first_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Nombre'
    )
    student_last_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Apellido'
    )
    course_type = models.CharField(
        max_length=10,
        choices=COURSE_TYPE_CHOICES,
        default=StudentProfile.COURSE_PPA_P,
        verbose_name='Tipo de curso'
    )
    #endregion

    #region INSTRUCTOR DATA
    instructor_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='ID instructor'
    )
    instructor_first_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Nombre'
    )
    instructor_last_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Apellido'
    )
    #endregion

    #region SESSION DATA
    session_date = models.DateField(
        default=timezone.now,
        verbose_name='Fecha'
    )
    flight_rules = models.CharField(
        max_length=4, 
        choices=FLIGHT_RULES_CHOICES,
        default=VFR,
        verbose_name='Reglas de vuelo'
    )
    pre_solo_flight = models.CharField(
        max_length=3,
        choices=PRE_SOLO_FLIGHT_CHOICES,
        default=NO,
        verbose_name='Sesión pre-solo'
    )
    session_number = models.CharField(
        max_length=3,
        choices=generate_choices(),
        default='1',
        verbose_name='Sesión'
    )
    session_letter = models.CharField(
        max_length=1,
        choices=SESSION_LETTER_CHOICES,
        blank=True,
        default='',
        verbose_name='Repetición de la sesión'
    )
    accumulated_sim_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        default=0.0,
        verbose_name='Horas de simulador acumuladas'
    )
    session_sim_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        default=0.0,   
        verbose_name='Horas sesión'
    )
    simulator = models.CharField(
        max_length=6,
        choices=SIMULATOR_CHOICES,
        default=FPT,
        verbose_name='Simulador'
    )
    session_grade = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Nota'
    )
    comments = models.TextField(blank=True, verbose_name='Comentarios', validators=[MinLengthValidator(75), MaxLengthValidator(1000)])
    #endregion

    def __str__(self):
        return f'{self.student_first_name} {self.student_last_name} - {self.session_date} - {self.simulator} - {self.session_grade}'
    
    class Meta:
        verbose_name = 'Bitácora de simulador'
        verbose_name_plural = 'Bitácoras de simulador'

class FlightLog(models.Model):
    """
    Flight Log Model

    This model receives data directly from the FlightEvaluation form.
    It generates records that allow students and authorized staff 
    to track and monitor students' flight training progress.
    """

    #region CHOICES DEFINITIONS

    # Course types
    COURSE_TYPE_CHOICES = StudentProfile.COURSE_TYPES

    # Session type
    SIM = 'SIMULADOR'
    FLIGHT = 'VUELO'

    SESSION_TYPE_CHOICES = [
        (SIM, 'SIMULADOR'),
        (FLIGHT, 'VUELO'),
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
    NO = 'NO'
    YES = 'SI'

    SOLO_FLIGHT_CHOICES = [
        (NO, 'NO'),
        (YES, 'SI'),
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
        ('C', 'C'),
    ]

    # Flight session grades
    SUPER_STANDARD = 'SS'
    STANDARD = 'S'
    NON_STANDARD = 'NS'
    NOT_EVALUATED = 'NE'

    SESSION_GRADE_CHOICES = [
        (SUPER_STANDARD, 'SS'),
        (STANDARD, 'S'),
        (NON_STANDARD, 'NS'),
        (NOT_EVALUATED, 'NE'),
    ]

    # Aircraft registration
    YV204E = 'YV204E'           
    YV206E = 'YV206E'

    AIRCRAFT_REG = [
        (YV204E, 'YV204E'),
        (YV206E, 'YV206E'),
    ]

    #endregion

    evaluation_id = models.PositiveIntegerField(
        verbose_name='ID',
        help_text='ID única de evaluación asociada',
    )

    evaluation_type = models.CharField(
        max_length=50,
        verbose_name='Tipo de evaluación',
        default='No type',
    )

    #region STUDENT DATA
    student_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='ID alumno'
    )
    student_first_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Nombre'
    )
    student_last_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Apellido'
    )
    course_type = models.CharField(
        max_length=10,
        choices=COURSE_TYPE_CHOICES,
        default=StudentProfile.COURSE_PPA_P,
        verbose_name='Tipo de curso'
    )
    #endregion

    #region INSTRUCTOR DATA
    instructor_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='ID instructor'
    )
    instructor_first_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Nombre'
    )
    instructor_last_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Apellido'
    )
    #endregion

    #region SESSION DATA
    session_date = models.DateField(
        default=timezone.now,
        verbose_name='Fecha'
    )
    flight_rules = models.CharField(
        max_length=4, 
        choices=FLIGHT_RULES_CHOICES,
        default=VFR,
        verbose_name='Reglas de vuelo'
    )
    solo_flight = models.CharField(
        max_length=3,
        choices=SOLO_FLIGHT_CHOICES,
        default=YES,
        verbose_name='Vuelo solo'
    )
    session_number = models.CharField(
        max_length=3,
        choices=generate_choices(),
        default='1',
        verbose_name='Sesión'
    )
    session_letter = models.CharField(
        max_length=1,
        choices=SESSION_LETTER_CHOICES,
        blank=True,
        default='',
        verbose_name='Repetición de la sesión'
    )
    accumulated_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        default=0.0,
        verbose_name='Horas de vuelo acumuladas'
    )
    session_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        default=0.0,   
        verbose_name='Horas sesión'
    )
    aircraft_registration = models.CharField(
        max_length=6,
        choices=AIRCRAFT_REG,
        default=YV204E,
        verbose_name='Aeronave'
    )
    session_grade = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Nota'
    )
    comments = models.TextField(blank=True, verbose_name='Comentarios', validators=[MinLengthValidator(75), MaxLengthValidator(1000)])
    #endregion

    def __str__(self):
        return f'{self.student_first_name} {self.student_last_name} - {self.session_date} - {self.aircraft_registration} - {self.session_flight_hours} hrs'
    
    class Meta:
        verbose_name = 'Bitácora de vuelo'
        verbose_name_plural = 'Bitácoras de vuelo'

class SimEvaluation(models.Model):
    """
    Simulator Evaluation Model

    This model receives data directly from the SimEvaluation form.
    It generates simulator session records that are used to generate pdf
    files and serve as a digital backup of simulator training sessions.
    """

    #region CHOICES DEFINITIONS

    # License types
    LICENSE_AP = 'AP'
    LICENSE_PPA = 'PPA'
    LICENSE_PCA = 'PCA'
    LICENSE_TLA = 'TLA'

    INSTRUCTOR_LICENSE_CHOICES = [ 
        (LICENSE_PCA, 'PCA'),
        (LICENSE_TLA, 'TLA'),
    ]

    STUDENT_LICENSE_CHOICES = [
        (LICENSE_AP, 'AP'),
        (LICENSE_PPA, 'PPA'),
        (LICENSE_PCA, 'PCA'),
        (LICENSE_TLA, 'TLA'),
    ]

    # Course types
    COURSE_TYPE_CHOICES = StudentProfile.COURSE_TYPES

    # Flight rules
    VFR = 'VFR'
    IFR = 'IFR'
    DUAL = 'DUAL'

    FLIGHT_RULES_CHOICES = [
        (VFR, 'VFR'),
        (IFR, 'IFR'),
        (DUAL, 'Dual'),
    ]

    # Pre-solo flight
    NO = 'NO'
    YES = 'SI'
 
    PRE_SOLO_FLIGHT_CHOICES = [
        (NO, 'NO'),
        (YES, 'SI'),
    ]

    # Simulator session grades
    SUPER_STANDARD = 'SS'
    STANDARD = 'S'
    NON_STANDARD = 'NS'
    NOT_EVALUATED = 'NE'

    SESSION_GRADE_CHOICES = [
        (SUPER_STANDARD, 'SS'),
        (STANDARD, 'S'),
        (NON_STANDARD, 'NS'),
        (NOT_EVALUATED, 'NE'),
    ]

    # Session number
    def generate_choices():
        choices = []
        for i in range(1, 11):
            choices.append((str(i), str(i)))
        return choices
    
    # Session letter
    SESSION_LETTER_CHOICES = [
        ('', ''),
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
    ]

    # Simulator
    FPT = 'FPT'
    B737 = 'B737'

    SIMULATOR_CHOICES = [
        (FPT, 'FPT'),
        (B737, 'B737'),
    ]
    #endregion

    #region STUDENT DATA
    student_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='ID alumno'
    )
    student_first_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Nombre'
    )
    student_last_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Apellido'
    )
    student_license_type = models.CharField(
        max_length=3,
        choices=STUDENT_LICENSE_CHOICES,
        default=None,
        verbose_name='Tipo de licencia'
    )
    student_license_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='Número de licencia'
    )
    course_type = models.CharField(
        max_length=10,
        choices=StudentProfile.COURSE_TYPES,
        default=StudentProfile.COURSE_PPA_P,
        verbose_name='Tipo de curso'
    )
    #endregion

    #region INSTRUCTOR DATA
    instructor_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='ID instructor'
    )
    instructor_first_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Nombre'
    )
    instructor_last_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Apellido'
    )
    instructor_license_type = models.CharField(
        max_length=3,
        choices=INSTRUCTOR_LICENSE_CHOICES,
        default=LICENSE_PCA,
        verbose_name='Tipo de licencia'
    )
    instructor_license_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='Número de licencia'
    )
    #endregion

    #region SESSION DATA
    session_date = models.DateField(
        default=timezone.now,
        verbose_name='Fecha'
    )
    flight_rules = models.CharField(
        max_length=4, 
        choices=FLIGHT_RULES_CHOICES,
        default=VFR,
        verbose_name='Reglas de vuelo'
    )
    pre_solo_flight = models.CharField(
        max_length=3,
        choices=PRE_SOLO_FLIGHT_CHOICES,
        default=NO,
        verbose_name='Sesión pre-solo'
    )
    session_number = models.CharField(
        max_length=3,
        choices=generate_choices(),
        default='1',
        verbose_name='Número'
    )
    session_letter = models.CharField(
        max_length=1,
        choices=SESSION_LETTER_CHOICES,
        blank=True,
        default='',
        verbose_name='Repetición de la sesión'
    )
    accumulated_sim_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        default=0.0,
        verbose_name='Horas de simulador acumuladas'
    )
    session_sim_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        default=0.0,
        verbose_name='Horas sesión'
    )
    simulator = models.CharField(
        max_length=6,
        choices=SIMULATOR_CHOICES,
        default=FPT,
        verbose_name='Simulador'
    )
    session_grade = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Nota'
    )
    #endregion

    #region PRE-FLIGHT
    pre_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Preparación del vuelo'
    )
    pre_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Lista de chequeo'
    )
    pre_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Instrucciones del ATC'
    )
    #endregion

    #region TAKEOFF
    to_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Uso de potencia'
    )
    to_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Rumbo'
    )
    to_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Actitud'
    )
    to_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Velocidad'
    )
    to_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Proc. de despegue'
    )
    #endregion

    #region DEPARTURE PROCEDURE
    dep_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Uso de radioayudas'
    )
    dep_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Radiocomunicaciones'
    )
    dep_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Instrucciones del ATC'
    )
    dep_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Conocimiento del SID'
    )
    dep_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Ejecución del SID'
    )
    #endregion

    #region BASIC INSTRUMENTS
    inst_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Ascenso'
    )
    inst_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Técnica de nivelado'
    )
    inst_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Vuelo recto y nivelado'
    )
    inst_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Virajes estándar'
    )
    inst_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Virajes 30° de banqueo'
    )
    inst_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Virajes 45° de banqueo'
    )
    inst_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='S vertical'
    )
    inst_8 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Cambios de velocidad'
    )
    inst_9 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Cambios de configuración'
    )
    inst_10 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Panel parcial'
    )
    inst_11 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Pérdida (conf. limpia)'
    )
    inst_12 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Pérdida (conf. despegue)'
    )
    inst_13 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Pérdida (conf. aterrizaje)'
    )
    #endregion

    #region UNUSUAL ACTITUDES
    upset_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Reconocimiento de actitud inusual'
    )
    upset_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Procedimiento de recuperación'
    )
    upset_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Uso de instrumentos'
    )
    #endregion

    #region MISCELLANEOUS
    misc_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Uso del transponder'
    )
    misc_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Teoría de vuelo instrumental'
    )
    misc_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Lectura e interpretación de cartas'
    )
    misc_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Uso del computador'
    )
    misc_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Conocimiento RAV'
    )
    misc_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Conocimiento general'
    )
    misc_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Uso de los compensadores'
    )
    #endregion

    #region RADIONAVIGATION AIDS (VOR)
    radio_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Sintonía para la identificación'
    )
    radio_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Intercepción IB'
    )
    radio_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Intercepción OB'
    )
    radio_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Tracking'
    )
    radio_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Entrada correcta'
    )
    radio_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Patrón de espera'
    )
    radio_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Virajes de procedimiento'
    )
    radio_8 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Estimación y corrección de tiempo'
    )
    radio_9 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Radiocomunicaciones'
    )
    radio_10 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Arco DME'
    )
    radio_11 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Técnica general'
    )
    #endregion

    #region RADIONAVIGATION AIDS (ADF)
    radio_12 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Sintonía para la identificación'
    )
    radio_13 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Intercepción IB'
    )
    radio_14 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Intercepción OB'
    )
    radio_15 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Tracking'
    )
    radio_16 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Entrada correcta'
    )
    radio_17 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Patrón de espera'
    )
    radio_18 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Virajes de procedimiento'
    )
    radio_19 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Estimación y corrección de tiempo'
    )
    radio_20 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Radiocomunicaciones'
    )
    radio_21 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Arco DME'
    )
    radio_22 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Técnica general'
    )
    #endregion

    #region APPROACH (ILS)
    app_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Instrucciones del ATC'
    )
    app_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Uso de frecuencias apropiadas'
    )
    app_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Radiocomunicaciones'
    )
    app_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Interpretación de cartas'
    )
    app_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Ejecución del procedimiento'
    )
    app_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Configuración'
    )
    app_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Aproximación frustrada'
    )
    app_8 = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Tipo de aproximación'
    )
    #endregion

    #region APPROACH (VOR)
    app_9 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Instrucciones del ATC'
    )
    app_10 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Uso de frecuencias apropiadas'
    )
    app_11 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Radiocomunicaciones'
    )
    app_12 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Interpretación de cartas'
    )
    app_13 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Ejecución del procedimiento'
    )
    app_14 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Configuración'
    )
    app_15 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Aproximación frustrada'
    )
    app_16 = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Tipo de aproximación'
    )
    #endregion

    #region APPROACH (ADF)
    app_17 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Instrucciones del ATC'
    )
    app_18 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Uso de frecuencias apropiadas'
    )
    app_19 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Radiocomunicaciones'
    )
    app_20 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Interpretación de cartas'
    )
    app_21 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Ejecución del procedimiento'
    )
    app_22 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Configuración'
    )
    app_23 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Aproximación frustrada'
    )
    app_24 = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Tipo de aproximación'
    )
    #endregion

    #region GO-AROUND
    go_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Ejecución del procedimiento'
    )
    go_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Comunicación'
    )
    #endregion

    comments = models.TextField(blank=True, verbose_name='Comentarios', validators=[MinLengthValidator(75), MaxLengthValidator(1000)])

    def total_sim_hours(self):
        """Return the sum of accumulated and session hours."""
        return self.accumulated_sim_hours + self.session_sim_hours

    def __str__(self):
        return f'{self.student_first_name} {self.student_last_name} - {self.session_date} - {self.simulator} - {self.session_sim_hours} hrs'
    
    def delete(self, *args, **kwargs):
        # Subtract session hours from student's accumulated hours
        try:
            student_profile = StudentProfile.objects.get(user__national_id=self.student_id)
            student_profile.sim_hours -= self.session_sim_hours
            # Ensure hours don't go negative
            if student_profile.sim_hours < 0:
                student_profile.sim_hours = 0
            student_profile.save()
        except StudentProfile.DoesNotExist:
            # If student profile doesn't exist, continue with deletion
            pass
        
        # Delete the associated SimulatorLog using the evaluation_id
        SimulatorLog.objects.filter(evaluation_id=self.id).delete()
    
        # Delete the evaluation record using the evaluation_id
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = 'Evaluación de simulador'
        verbose_name_plural = 'Evaluaciones de simulador'

class FlightEvaluation0_100(models.Model):
    """
    Flight Evaluation Model

    This model receives data directly from the FlightEvaluation form.
    It generates flight session records that are used to generate pdf
    files and serve as a digital backup of flight training sessions.
    """

    #region CHOICES DEFINITIONS

    # License types
    LICENSE_AP = 'AP'
    LICENSE_PPA = 'PPA'
    LICENSE_PCA = 'PCA'
    LICENSE_TLA = 'TLA'

    INSTRUCTOR_LICENSE_CHOICES = [ 
        (LICENSE_PCA, 'PCA'),
        (LICENSE_TLA, 'TLA'),
    ]

    STUDENT_LICENSE_CHOICES = [
        (LICENSE_AP, 'AP'),
        (LICENSE_PPA, 'PPA'),
        (LICENSE_PCA, 'PCA'),
        (LICENSE_TLA, 'TLA'),
    ]

    # Course types
    COURSE_TYPE_CHOICES = StudentProfile.COURSE_TYPES

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
    NO = 'NO'
    YES = 'SI'
 
    SOLO_FLIGHT_CHOICES = [
        (NO, 'NO'),
        (YES, 'SI'),
    ]

    # Flight session grades
    SUPER_STANDARD = 'SS'
    STANDARD = 'S'
    NON_STANDARD = 'NS'
    NOT_EVALUATED = 'NE'

    SESSION_GRADE_CHOICES = [
        (SUPER_STANDARD, 'SS'),
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
        ('C', 'C'),
    ]

    # Aircraft registration
    YV204E = 'YV204E'
    YV206E = 'YV206E'

    AIRCRAFT_REG = [
        (YV204E, 'YV204E'),
        (YV206E, 'YV206E'),
    ]
    #endregion

    #region STUDENT DATA
    student_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='ID alumno'
    )
    student_first_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Nombre'
    )
    student_last_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Apellido'
    )
    student_license_type = models.CharField(
        max_length=3,
        choices=STUDENT_LICENSE_CHOICES,
        default=None,
        verbose_name='Tipo de licencia'
    )
    student_license_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='Número de licencia'
    )
    course_type = models.CharField(
        max_length=10,
        choices=StudentProfile.COURSE_TYPES,
        default=StudentProfile.COURSE_PPA_P,
        verbose_name='Tipo de curso'
    )
    #endregion

    #region INSTRUCTOR DATA
    instructor_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='ID instructor'
    )
    instructor_first_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Nombre'
    )
    instructor_last_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Apellido'
    )
    instructor_license_type = models.CharField(
        max_length=3,
        choices=INSTRUCTOR_LICENSE_CHOICES,
        default=LICENSE_PCA,
        verbose_name='Tipo de licencia'
    )
    instructor_license_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='Número de licencia'
    )
    #endregion

    #region SESSION DATA
    session_date = models.DateField(
        default=timezone.now,
        verbose_name='Fecha'
    )
    flight_rules = models.CharField(
        max_length=4, 
        choices=FLIGHT_RULES_CHOICES,
        default=VFR,
        verbose_name='Reglas de vuelo'
    )
    solo_flight = models.CharField(
        max_length=3,
        choices=SOLO_FLIGHT_CHOICES,
        default=NO,
        verbose_name='Vuelo solo'
    )
    session_number = models.CharField(
        max_length=3,
        choices=generate_choices(),
        default='1',
        verbose_name='Número'
    )
    session_letter = models.CharField(
        max_length=1,
        choices=SESSION_LETTER_CHOICES,
        blank=True,
        default='',
        verbose_name='Repetición de la sesión'
    )
    accumulated_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        default=0.0,
        verbose_name='Horas de vuelo acumuladas'
    )
    session_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        default=0.0,
        verbose_name='Horas sesión'
    )
    aircraft_registration = models.CharField(
        max_length=6,
        choices=AIRCRAFT_REG,
        default=YV204E,
        verbose_name='Aeronave'
    )
    session_grade = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Nota'
    )
    #endregion

    #region PRE-FLIGHT
    pre_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Plan de vuelo VFR'
    )
    pre_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Inspección pre-vuelo'
    )
    pre_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Uso correcto de checklist'
    )
    pre_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Comunicaciones aeronáuticas'
    )
    pre_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Técnica de rodaje'
    )
    pre_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Anormalidades en el encendido y taxeo'
    )
    #endregion

    #region TAKEOFF
    to_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Normal/Estático/Rolling'
    )
    to_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Viento cruzado'
    )
    to_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Pista corta y/o campo blando'
    )
    to_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Ascenso (potencia/velocidad/rumbo)'
    )
    to_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Comunicaciones aeronáuticas'
    )
    to_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Ejecución salida visual'
    )
    #endregion

    #region MANEUVERS
    mvrs_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Uso de compensadores'
    )
    mvrs_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Técnica de nivelado (control y comportamiento)'
    )
    mvrs_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Vuelto recto nivelado'
    )
    mvrs_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Virajes de 10, 20, 30 y 45'
    )
    mvrs_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Virajes ascenso/descenso'
    )
    mvrs_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Vuelo lento'
    )
    mvrs_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Pérdida limpia'
    )
    mvrs_8 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Pérdida config. despegue y aterrizaje'
    )
    mvrs_9 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Pérdida secundaria'
    )
    mvrs_10 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Efecto del P-factor'
    )
    mvrs_11 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Chandelles'
    )
    mvrs_12 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='8 perezosos'
    )
    mvrs_13 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='S sobre pilones'
    )
    mvrs_14 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='S sobre carreteras'
    )
    mvrs_15 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Descenso c/s potencia (glide speed)'
    )
    mvrs_16 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Ubicación espacial'
    )
    mvrs_17 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Reconocimiento de actitud inusual (UPSET)'
    )
    mvrs_18 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Precisión de 090, 180, 360 y 720'
    )
    #endregion

    #region NAVIGATION VFR
    nav_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Briefing de pre-vuelo'
    )
    nav_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Planificación/Tablas de performance'
    )
    nav_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Plan de vuelo operacional (TOC-TOD)'
    )
    nav_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Comunicaciones en ruta (reportes)'
    )
    nav_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Orientación espacial'
    )
    nav_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Uso de radioayudas'
    )
    #endregion

    #region CIRCUIT/PROCEDURE
    land_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Comunicación'
    )
    land_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Procedimiento de circuito'
    )
    land_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Maniobra de derrape (demo)'
    )
    land_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Configuración de aterrizaje (limpio/full flaps)'
    )
    land_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Aproximación estabilizada'
    )
    land_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Aterrizaje normal'
    )
    land_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Aterrizaje corto/campo suave'
    )
    land_8 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Toque y despegue'
    )
    land_9 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Go-around'
    )
    land_10 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Situaciones anormales en el circuito'
    )
    #endregion

    #region EMERGENCIES
    emer_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Actitud y juicio'
    )
    emer_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Identificación de la anormalidad'
    )
    emer_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Procedimientos memory-items y anormales'
    )
    emer_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Control de la aeronave'
    )
    emer_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Navegación (plan alterno en ruta)'
    )
    emer_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Comunicaciones'
    )
    #endregion

    #region GENERAL
    gen_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Actitud y criterio'
    )
    gen_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Seguridad de vuelo'
    )
    gen_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Disciplina de vuelo'
    )
    gen_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Técnica de vuelo'
    )
    gen_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Conocimiento de la aeronave y limitaciones'
    )
    gen_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Conocimiento RAV'
    )
    gen_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Juicio general'
    )
    #endregion

    comments = models.TextField(blank=True, verbose_name='Comentarios', validators=[MinLengthValidator(75), MaxLengthValidator(1000)])

    def total_flight_hours(self):
        """Return the sum of accumulated and session flight hours."""
        return self.accumulated_flight_hours + self.session_flight_hours

    def __str__(self):
        return f'{self.student_first_name} {self.student_last_name} - {self.session_date} - {self.aircraft_registration} - {self.session_flight_hours} hrs'
    
    def delete(self, *args, **kwargs):
        # Subtract session hours from student's accumulated hours
        try:
            student_profile = StudentProfile.objects.get(user__national_id=self.student_id)
            student_profile.flight_hours -= self.session_flight_hours
            # Ensure hours don't go negative
            if student_profile.flight_hours < 0:
                student_profile.flight_hours = 0
            student_profile.save()
        except StudentProfile.DoesNotExist:
            # If student profile doesn't exist, continue with deletion
            pass
        
        # Delete the associated FlightLog using the evaluation_id
        FlightLog.objects.filter(
            evaluation_id=self.id,
            evaluation_type='FlightEvaluation0_100'
        ).delete()
    
        # Delete the evaluation record using the primary id
        super().delete(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Evaluación de vuelo 0-100'
        verbose_name_plural = 'Evaluaciones de vuelo 0-100'

class FlightEvaluation100_120(models.Model):
    """
    Flight Evaluation Model

    This model receives data directly from the FlightEvaluation form.
    It generates flight session records that are used to generate pdf
    files and serve as a digital backup of flight training sessions.
    """

    #region CHOICES DEFINITIONS

    # License types
    LICENSE_AP = 'AP'
    LICENSE_PPA = 'PPA'
    LICENSE_PCA = 'PCA'
    LICENSE_TLA = 'TLA'

    INSTRUCTOR_LICENSE_CHOICES = [ 
        (LICENSE_PCA, 'PCA'),
        (LICENSE_TLA, 'TLA'),
    ]

    STUDENT_LICENSE_CHOICES = [
        (LICENSE_AP, 'AP'),
        (LICENSE_PPA, 'PPA'),
        (LICENSE_PCA, 'PCA'),
        (LICENSE_TLA, 'TLA'),
    ]

    # Course types
    COURSE_TYPE_CHOICES = StudentProfile.COURSE_TYPES

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
    NO = 'NO'
    YES = 'SI'
 
    SOLO_FLIGHT_CHOICES = [
        (NO, 'NO'),
        (YES, 'SI'),
    ]

    # Flight session grades
    SUPER_STANDARD = 'SS'
    STANDARD = 'S'
    NON_STANDARD = 'NS'
    NOT_EVALUATED = 'NE'

    SESSION_GRADE_CHOICES = [
        (SUPER_STANDARD, 'SS'),
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
        ('C', 'C'),
    ]

    # Aircraft registration
    YV204E = 'YV204E'
    YV206E = 'YV206E'

    AIRCRAFT_REG = [
        (YV204E, 'YV204E'),
        (YV206E, 'YV206E'),
    ]
    #endregion

    #region STUDENT DATA
    student_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='ID alumno'
    )
    student_first_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Nombre'
    )
    student_last_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Apellido'
    )
    student_license_type = models.CharField(
        max_length=3,
        choices=STUDENT_LICENSE_CHOICES,
        default=None,
        verbose_name='Tipo de licencia'
    )
    student_license_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='Número de licencia'
    )
    course_type = models.CharField(
        max_length=10,
        choices=StudentProfile.COURSE_TYPES,
        default=StudentProfile.COURSE_HVI_P,
        verbose_name='Tipo de curso'
    )
    #endregion

    #region INSTRUCTOR DATA
    instructor_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='ID instructor'
    )
    instructor_first_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Nombre'
    )
    instructor_last_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Apellido'
    )
    instructor_license_type = models.CharField(
        max_length=3,
        choices=INSTRUCTOR_LICENSE_CHOICES,
        default=LICENSE_PCA,
        verbose_name='Tipo de licencia'
    )
    instructor_license_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='Número de licencia'
    )
    #endregion

    #region SESSION DATA
    session_date = models.DateField(
        default=timezone.now,
        verbose_name='Fecha'
    )
    flight_rules = models.CharField(
        max_length=4, 
        choices=FLIGHT_RULES_CHOICES,
        default=VFR,
        verbose_name='Reglas de vuelo'
    )
    solo_flight = models.CharField(
        max_length=3,
        choices=SOLO_FLIGHT_CHOICES,
        default=NO,
        verbose_name='Vuelo solo'
    )
    session_number = models.CharField(
        max_length=3,
        choices=generate_choices(),
        default='1',
        verbose_name='Número'
    )
    session_letter = models.CharField(
        max_length=1,
        choices=SESSION_LETTER_CHOICES,
        blank=True,
        default='',
        verbose_name='Repetición de la sesión'
    )
    accumulated_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        default=0.0,
        verbose_name='Horas de vuelo acumuladas'
    )
    session_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        default=0.0,
        verbose_name='Horas sesión'
    )
    aircraft_registration = models.CharField(
        max_length=6,
        choices=AIRCRAFT_REG,
        default=YV204E,
        verbose_name='Aeronave'
    )
    session_grade = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Nota'
    )
    #endregion

    #region PRE-FLIGHT
    pre_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Plan de vuelo IFR'
    )
    pre_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Inspección pre-vuelo'
    )
    pre_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Uso correcto de checklist'
    )
    pre_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Comunicaciones aeronáuticas'
    )
    pre_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Técnica de rodaje'
    )
    pre_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Anormalidades en el encendido y taxeo'
    )
    #endregion

    #region TAKEOFF/INSTRUMENT DEPARTURE
    to_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Normal'
    )
    to_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Viento cruzado'
    )
    to_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Pista corta'
    )
    to_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Ascenso (potencia/velocidad/rumbo)'
    )
    to_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Comunicaciones aeronáuticas IFR'
    )
    to_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Ejecución SID'
    )
    #endregion

    #region BASIC IFR PROCEDURES
    b_ifr_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Maniobra tipo S (SA, SB, SC, SD)'
    )
    b_ifr_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Virajes cronometrados (1 RST / 1/2 RST)'
    )
    b_ifr_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Reconocimiento de actitud inusual (UPSET)'
    )
    b_ifr_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Serie de virajes'
    )
    b_ifr_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Cambios de velocidad'
    )
    b_ifr_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Intercepción de radiales (IB/OB)'
    )
    b_ifr_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Interceptación de marcaciones'
    )
    b_ifr_8 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Uso de instrumentos de navegación (chequeos)'
    )
    b_ifr_9 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Chequeo cruzado'
    )
    b_ifr_10 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Virajes inversión curso (45x180) (80x260) (base)'
    )
    b_ifr_11 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Patrón de juego'
    )
    #endregion

    #region ADVANCED IFR PROCEDURES
    a_ifr_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Plan de vuelo/operacional (IFR)'
    )
    a_ifr_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Planificación IFR'
    )
    a_ifr_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Comunicaciones IFR (reportes)'
    )
    a_ifr_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Ejecución SID'
    )
    a_ifr_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Viraje de procedimiento (45x180) (base)'
    )
    a_ifr_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Arcos/DME'
    )
    a_ifr_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Procedimientos de no-precisión'
    )
    a_ifr_8 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Procedimientos APV (demo)'
    )
    a_ifr_9 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Procedimientos de precisión'
    )
    a_ifr_10 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Procedimiento de aprox. frustrada'
    )
    a_ifr_11 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Circuitos de espera'
    )
    #endregion

    #region FINAL APPROACH/LANDING
    land_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Aterrizaje normal'
    )
    land_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Aproximación estabilizada'
    )
    land_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Aproximación frustrada'
    )
    land_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Ejecución de procedimiento IFR'
    )
    land_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Transición IFR a referencias visuales'
    )
    land_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Disciplina de vuelo'
    )
    land_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Técnica de vuelo'
    )
    #endregion

    #region EMERGENCIES
    emer_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Actitud y juicio'
    )
    emer_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Identificación de la anormalidad'
    )
    emer_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Procedimientos memory-items y anormales'
    )
    emer_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Recuperación de pérdida por instrumentos'
    )
    emer_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Panel parcial'
    )
    #endregion

    #region GENERAL
    gen_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Actitud y criterio'
    )
    gen_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Seguridad de vuelo'
    )
    gen_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Disciplina de vuelo'
    )
    gen_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Técnica de vuelo'
    )
    gen_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Conocimiento de la aeronave y limitaciones'
    )
    gen_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Conocimiento RAV'
    )
    gen_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Juicio general'
    )
    #endregion

    comments = models.TextField(blank=True, verbose_name='Comentarios', validators=[MinLengthValidator(75), MaxLengthValidator(1000)])

    def total_flight_hours(self):
        """Return the sum of accumulated and session flight hours."""
        return self.accumulated_flight_hours + self.session_flight_hours

    def __str__(self):
        return f'{self.student_first_name} {self.student_last_name} - {self.session_date} - {self.aircraft_registration} - {self.session_flight_hours} hrs'
    
    def delete(self, *args, **kwargs):
        # Subtract session hours from student's accumulated hours
        try:
            student_profile = StudentProfile.objects.get(user__national_id=self.student_id)
            student_profile.flight_hours -= self.session_flight_hours
            # Ensure hours don't go negative
            if student_profile.flight_hours < 0:
                student_profile.flight_hours = 0
            student_profile.save()
        except StudentProfile.DoesNotExist:
            # If student profile doesn't exist, continue with deletion
            pass
        
        # Delete the associated FlightLog using the evaluation_id
        FlightLog.objects.filter(
            evaluation_id=self.id,
            evaluation_type='FlightEvaluation100_120'
        ).delete()
    
        # Delete the evaluation record using the evaluation_id
        super().delete(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Evaluación de vuelo 100-120'
        verbose_name_plural = 'Evaluaciones de vuelo 100-120'

class FlightEvaluation120_170(models.Model):
    """
    Flight Evaluation Model

    This model receives data directly from the FlightEvaluation form.
    It generates flight session records that are used to generate pdf
    files and serve as a digital backup of flight training sessions.
    """

    #region CHOICES DEFINITIONS

    # License types
    LICENSE_AP = 'AP'
    LICENSE_PPA = 'PPA'
    LICENSE_PCA = 'PCA'
    LICENSE_TLA = 'TLA'

    INSTRUCTOR_LICENSE_CHOICES = [ 
        (LICENSE_PCA, 'PCA'),
        (LICENSE_TLA, 'TLA'),
    ]

    STUDENT_LICENSE_CHOICES = [
        (LICENSE_AP, 'AP'),
        (LICENSE_PPA, 'PPA'),
        (LICENSE_PCA, 'PCA'),
        (LICENSE_TLA, 'TLA'),
    ]

    # Course types
    COURSE_TYPE_CHOICES = StudentProfile.COURSE_TYPES

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
    NO = 'NO'
    YES = 'SI'
 
    SOLO_FLIGHT_CHOICES = [
        (NO, 'NO'),
        (YES, 'SI'),
    ]

    # Flight session grades
    SUPER_STANDARD = 'SS'
    STANDARD = 'S'
    NON_STANDARD = 'NS'
    NOT_EVALUATED = 'NE'

    SESSION_GRADE_CHOICES = [
        (SUPER_STANDARD, 'SS'),
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
        ('C', 'C'),
    ]

    # Aircraft registration
    YV204E = 'YV204E'
    YV206E = 'YV206E'

    AIRCRAFT_REG = [
        (YV204E, 'YV204E'),
        (YV206E, 'YV206E'),
    ]
    #endregion

    #region STUDENT DATA
    student_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='ID alumno'
    )
    student_first_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Nombre'
    )
    student_last_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Apellido'
    )
    student_license_type = models.CharField(
        max_length=3,
        choices=STUDENT_LICENSE_CHOICES,
        default=None,
        verbose_name='Tipo de licencia'
    )
    student_license_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='Número de licencia'
    )
    course_type = models.CharField(
        max_length=10,
        choices=StudentProfile.COURSE_TYPES,
        default=StudentProfile.COURSE_PCA_P,
        verbose_name='Tipo de curso'
    )
    #endregion

    #region INSTRUCTOR DATA
    instructor_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='ID instructor'
    )
    instructor_first_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Nombre'
    )
    instructor_last_name = models.CharField(
        max_length=50,
        default='',
        verbose_name='Apellido'
    )
    instructor_license_type = models.CharField(
        max_length=3,
        choices=INSTRUCTOR_LICENSE_CHOICES,
        default=LICENSE_PCA,
        verbose_name='Tipo de licencia'
    )
    instructor_license_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        verbose_name='Número de licencia'
    )
    #endregion

    #region SESSION DATA
    session_date = models.DateField(
        default=timezone.now,
        verbose_name='Fecha'
    )
    flight_rules = models.CharField(
        max_length=4, 
        choices=FLIGHT_RULES_CHOICES,
        default=VFR,
        verbose_name='Reglas de vuelo'
    )
    solo_flight = models.CharField(
        max_length=3,
        choices=SOLO_FLIGHT_CHOICES,
        default=NO,
        verbose_name='Vuelo solo'
    )
    session_number = models.CharField(
        max_length=3,
        choices=generate_choices(),
        default='1',
        verbose_name='Número'
    )
    session_letter = models.CharField(
        max_length=1,
        choices=SESSION_LETTER_CHOICES,
        blank=True,
        default='',
        verbose_name='Repetición de la sesión'
    )
    accumulated_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        default=0.0,
        verbose_name='Horas de vuelo acumuladas'
    )
    session_flight_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        default=0.0,
        verbose_name='Horas sesión'
    )
    aircraft_registration = models.CharField(
        max_length=6,
        choices=AIRCRAFT_REG,
        default=YV204E,
        verbose_name='Aeronave'
    )
    session_grade = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Nota'
    )
    #endregion

    #region PRE-FLIGHT
    pre_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Plan de vuelo VFR/IFR'
    )
    pre_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Insp. pre-vuelo / briefing (Serv/WX/NOTAMs)'
    )
    pre_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Uso correcto de checklist'
    )
    pre_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Comns. IFR (ICAO 4) (ATIS/Clearance)'
    )
    pre_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Técnica de rodaje/hotspot/lectura taxi-route'
    )
    pre_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Anormalidades en el encendido y taxeo'
    )
    #endregion

    #region TAKEOFF/INSTRUMENT DEPARTURE
    to_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Normal'
    )
    to_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Viento cruzado'
    )
    to_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Pista corta y/o suave'
    )
    to_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Ascenso (potencia/velocidad/rumbo)'
    )
    to_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Comns. IFR (ICAO 4)'
    )
    to_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Ejecución SID (salidas vectorizadas)'
    )
    #endregion

    #region ADVANCED IFR PROCEDURES
    inst_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Plan de vuelo/operacional (IFR)'
    )
    inst_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Planificación IFR'
    )
    inst_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Comns. IFR (ICAO 4) (ATIS/Clearance)'
    )
    inst_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Radionavegación convencional/RNAV'
    )
    inst_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Viraje de procedimiento (45x180) (base)'
    )
    inst_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Arcos/DME'
    )
    inst_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Procedimientos de no-precisión'
    )
    inst_8 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Procedimientos APV (demo)'
    )
    inst_9 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Procedimientos de precisión'
    )
    inst_10 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Procedimiento de aprox. frustrada'
    )
    inst_11 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Circuitos de espera'
    )
    #endregion

    #region FINAL APPROACH/LANDING
    land_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Aterrizaje normal'
    )
    land_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Aproximación estabilizada'
    )
    land_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Aproximación frustrada'
    )
    land_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Ejecución de procedimiento IFR'
    )
    land_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Transición IFR a referencias visuales'
    )
    land_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Procedimiento taxi out'
    )
    land_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Técnica de vuelo'
    )
    #endregion

    #region EMERGENCIES
    emer_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Windshear'
    )
    emer_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Evento TCAS'
    )
    emer_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Incapacitación del piloto'
    )
    emer_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Sin radiocomunicaciones abordo (NORDO)'
    )
    #endregion

    #region GENERAL
    gen_1 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Actitud y criterio'
    )
    gen_2 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Seguridad de vuelo'
    )
    gen_3 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Disciplina de vuelo'
    )
    gen_4 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Técnica de vuelo'
    )
    gen_5 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Conocimiento de la aeronave y limitaciones'
    )
    gen_6 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Conocimiento RAV'
    )
    gen_7 = models.CharField(
        max_length=2,
        choices=SESSION_GRADE_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Juicio general'
    )
    #endregion

    comments = models.TextField(blank=True, verbose_name='Comentarios', validators=[MinLengthValidator(75), MaxLengthValidator(1000)])

    def total_flight_hours(self):
        """Return the sum of accumulated and session flight hours."""
        return self.accumulated_flight_hours + self.session_flight_hours

    def __str__(self):
        return f'{self.student_first_name} {self.student_last_name} - {self.session_date} - {self.aircraft_registration} - {self.session_flight_hours} hrs'

    def delete(self, *args, **kwargs):
        # Subtract session hours from student's accumulated hours
        try:
            student_profile = StudentProfile.objects.get(user__national_id=self.student_id)
            student_profile.flight_hours -= self.session_flight_hours
            # Ensure hours don't go negative
            if student_profile.flight_hours < 0:
                student_profile.flight_hours = 0
            student_profile.save()
        except StudentProfile.DoesNotExist:
            # If student profile doesn't exist, continue with deletion
            pass
        
        # Delete the associated FlightLog using the evaluation_id
        FlightLog.objects.filter(
            evaluation_id=self.id,
            evaluation_type='FlightEvaluation120_170'
        ).delete()
    
        # Delete the evaluation record using the evaluation_id
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = 'Evaluación de vuelo 120-170'
        verbose_name_plural = 'Evaluaciones de vuelo 120-170'