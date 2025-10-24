from django import forms
from django.db import transaction
from .models import FlightEvaluation0_100, FlightEvaluation100_120, FlightEvaluation120_170, SimEvaluation, FlightReport
from accounts.models import StudentProfile
from fleet.models import Simulator, Aircraft
import decimal

class SimEvaluationForm(forms.ModelForm):
    # Add a custom simulator field that uses ModelChoiceField
    simulator = forms.ModelChoiceField(
        queryset=Simulator.objects.filter(is_active=True),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-field'}),
        label='Simulador'
    )
    
    # Custom session_sim_hours field with input constraints
    session_sim_hours = forms.DecimalField(
        max_digits=3,
        decimal_places=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-field',
            'step': '0.1',
            'min': '0',
            'max': '4.0',
            'maxlength': '3'
        }),
        label='Horas sesión'
    )
    
    class Meta:
        model = SimEvaluation
        fields = [
            'instructor_id', 'instructor_first_name', 'instructor_last_name',
            'instructor_license_type', 'instructor_license_number',
            'student_id', 'student_first_name', 'student_last_name',
            'student_license_type', 'course_type',
            'flight_rules', 'pre_solo_flight', 'session_number', 'session_letter', 'session_date',
            'accumulated_sim_hours', 'session_sim_hours', 'simulator', 'session_type', 'session_grade',
            'pre_1', 'pre_2', 'pre_3',
            'to_1', 'to_2', 'to_3', 'to_4', 'to_5',
            'dep_1', 'dep_2', 'dep_3', 'dep_4', 'dep_5',
            'inst_1', 'inst_2', 'inst_3', 'inst_4', 'inst_5', 'inst_6', 'inst_7', 
            'inst_8', 'inst_9', 'inst_10', 'inst_11', 'inst_12', 'inst_13',
            'upset_1', 'upset_2', 'upset_3',
            'misc_1', 'misc_2', 'misc_3', 'misc_4', 'misc_5', 'misc_6', 'misc_7',
            'radio_1', 'radio_2', 'radio_3', 'radio_4', 'radio_5', 'radio_6',
            'radio_7', 'radio_8', 'radio_9', 'radio_10', 'radio_11', 'radio_12',
            'radio_13', 'radio_14', 'radio_15', 'radio_16', 'radio_17', 'radio_18',
            'radio_19', 'radio_20', 'radio_21', 'radio_22',
            'app_1', 'app_2', 'app_3', 'app_4', 'app_5', 'app_6', 'app_7', 'app_8',
            'app_9', 'app_10', 'app_11', 'app_12', 'app_13', 'app_14', 'app_15', 'app_16',
            'app_17', 'app_18', 'app_19', 'app_20', 'app_21', 'app_22', 'app_23', 'app_24',
            'go_1', 'go_2',
            'comments',
        ]

        labels = {
            'instructor_id': 'Número de cédula',
            'instructor_first_name': 'Nombre',
            'instructor_last_name': 'Apellido',
            'instructor_license_type': 'Tipo de licencia',
            'instructor_license_number': 'Número de licencia',
            'student_id': 'Número de cédula',
            'student_first_name': 'Nombre',
            'student_last_name': 'Apellido',
            'student_license_type': 'Tipo de licencia',
            'course_type': 'Curso',
            'flight_rules': 'Reglas de vuelo',
            'pre_solo_flight': 'Sesión pre-solo',
            'session_number': 'Número de sesión',
            'session_letter': 'Repetición de la sesión',
            'session_date': 'Fecha de la sesión',
            'accumulated_sim_hours': 'Horas de sim. totales',
            'session_sim_hours': 'Horas de la sesión',
            'simulator': 'Simulador',
            'session_type': 'Tipo de sesión',
            'session_grade': 'Calificación de la sesión',
            'pre_1': 'Preparación del vuelo',
            'pre_2': 'Lista de chequeo',
            'pre_3': 'Instrucciones del ATC',
            'to_1': 'Uso de potencia',
            'to_2': 'Rumbo',
            'to_3': 'Actitud',
            'to_4': 'Velocidad',
            'to_5': 'Procedimiento de despegue',
            'dep_1': 'Uso de radioayudas',
            'dep_2': 'Radiocomunicaciones',
            'dep_3': 'Instrucciones del ATC',
            'dep_4': 'Conocimiento del SID',
            'dep_5': 'Ejecución del SID',
            'inst_1': 'Ascenso',
            'inst_2': 'Técnica de nivelado',
            'inst_3': 'Vuelo recto y nivelado',
            'inst_4': 'Virajes estándar',
            'inst_5': 'Virajes 30° de banqueo',
            'inst_6': 'Virajes 45° de banqueo',
            'inst_7': 'S vertical',
            'inst_8': 'Cambios de velocidad',
            'inst_9': 'Cambios de configuración',
            'inst_10': 'Panel parcial',
            'inst_11': 'Pérdida (conf. limpia)',
            'inst_12': 'Pérdida (conf. despegue)',
            'inst_13': 'Pérdida (conf. aterrizaje)',
            'upset_1': 'Reconocimiento de actitud inusual',
            'upset_2': 'Procedimiento de recuperación',
            'upset_3': 'Uso de instrumentos',
            'misc_1': 'Uso del transponder',
            'misc_2': 'Teoría de vuelo instrumental',
            'misc_3': 'Lectura e interpretación de cartas',
            'misc_4': 'Uso del computador',
            'misc_5': 'Conocimiento RAV',
            'misc_6': 'Conocimiento general',
            'misc_7': 'Uso de los compensadores',
            'radio_1': 'Sintonía para la identificación',
            'radio_2': 'Intercepción IB',
            'radio_3': 'Intercepción OB',
            'radio_4': 'Tracking',
            'radio_5': 'Entrada correcta',
            'radio_6': 'Patrón de espera',
            'radio_7': 'Viraje de procedimiento',
            'radio_8': 'Estimación y corrección de tiempo',
            'radio_9': 'Radiocomunicaciones',
            'radio_10': 'Arco DME',
            'radio_11': 'Técnica general',
            'radio_12': 'Sintonía para la identificación',
            'radio_13': 'Intercepción IB',
            'radio_14': 'Intercepción OB',
            'radio_15': 'Tracking',
            'radio_16': 'Entrada correcta',
            'radio_17': 'Patrón de espera',
            'radio_18': 'Viraje de procedimiento',
            'radio_19': 'Estimación y corrección de tiempo',
            'radio_20': 'Radiocomunicaciones',
            'radio_21': 'Arco DME',
            'radio_22': 'Técnica general',
            'app_1': 'Instrucciones del ATC',
            'app_2': 'Uso de frecuencias apropiadas',
            'app_3': 'Radiocomunicaciones',
            'app_4': 'Interpretación de cartas',
            'app_5': 'Ejecución del procedimiento',
            'app_6': 'Configuración',
            'app_7': 'Aproximación frustrada',
            'app_8': 'Tipo de aproximación',
            'app_9': 'Instrucciones del ATC',
            'app_10': 'Uso de frecuencias apropiadas',
            'app_11': 'Radiocomunicaciones',
            'app_12': 'Interpretación de cartas',
            'app_13': 'Ejecución del procedimiento',
            'app_14': 'Configuración',
            'app_15': 'Aproximación frustrada',
            'app_16': 'Tipo de aproximación',
            'app_17': 'Instrucciones del ATC',
            'app_18': 'Uso de frecuencias apropiadas',
            'app_19': 'Radiocomunicaciones',
            'app_20': 'Interpretación de cartas',
            'app_21': 'Ejecución del procedimiento',
            'app_22': 'Configuración',
            'app_23': 'Aproximación frustrada',
            'app_24': 'Tipo de aproximación',
            'go_1': 'Ejecución del procedimiento',
            'go_2': 'Comunicación',
            'comments': '',
        }

        widgets = {
            'instructor_id': forms.NumberInput(attrs={'class': 'form-field'}),
            'instructor_first_name': forms.TextInput(attrs={'class': 'form-field'}),
            'instructor_last_name': forms.TextInput(attrs={'class': 'form-field'}),
            'instructor_license_type': forms.Select(attrs={'class': 'form-field'}),
            'instructor_license_number': forms.NumberInput(attrs={'class': 'form-field'}),
            'student_id': forms.NumberInput(attrs={'class': 'form-field'}),
            'student_first_name': forms.TextInput(attrs={'class': 'form-field'}),
            'student_last_name': forms.TextInput(attrs={'class': 'form-field'}),
            'student_license_type': forms.Select(attrs={'class': 'form-field'}),
            'course_type': forms.Select(attrs={'class': 'form-field'}),
            'flight_rules': forms.Select(attrs={'class': 'form-field'}),
            'pre_solo_flight': forms.Select(attrs={'class': 'form-field'}),
            'session_number': forms.Select(attrs={'class': 'form-field'}),
            'session_letter': forms.Select(attrs={'class': 'form-field'}),
            'session_date': forms.DateInput(attrs={'class': 'form-field', 'type': 'date'}),
            'accumulated_sim_hours': forms.TextInput(attrs={'class': 'form-field'}),
            'session_sim_hours': forms.NumberInput(attrs={'class': 'form-field'}),
            'session_type': forms.Select(attrs={'class': 'form-field'}),
            'session_grade': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'dep_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'dep_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'dep_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'dep_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'dep_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_7': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_8': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_9': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_10': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_11': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_12': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_13': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'upset_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'upset_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'upset_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'misc_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'misc_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'misc_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'misc_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'misc_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'misc_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'misc_7': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_7': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_8': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_9': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_10': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_11': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_12': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_13': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_14': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_15': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_16': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_17': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_18': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_19': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_20': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_21': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'radio_22': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_7': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_8': forms.TextInput(attrs={'class': 'form-field'}),
            'app_9': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_10': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_11': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_12': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_13': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_14': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_15': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_16': forms.TextInput(attrs={'class': 'form-field'}),
            'app_17': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_18': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_19': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_20': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_21': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_22': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_23': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'app_24': forms.TextInput(attrs={'class': 'form-field'}),
            'go_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'go_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'comments': forms.Textarea(attrs={'class': 'form-field', 'rows': 10, 'placeholder': 'Mínimo 75 caracteres, máximo 1000 caracteres'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extract the 'user' argument from kwargs
        super().__init__(*args, **kwargs)
        
        # Set student fields to empty to prevent preselection
        self.fields['student_license_type'].initial = ''
        self.fields['course_type'].initial = ''
        
        # Override the field choices to include empty option
        self.fields['student_license_type'].choices = [('', '---------')] + list(self.fields['student_license_type'].choices)
        self.fields['course_type'].choices = [('', '---------')] + list(self.fields['course_type'].choices)
        
        if user:
            profile = user.instructor_profile
            self.fields['instructor_id'].initial = user.national_id
            self.fields['instructor_first_name'].initial = user.first_name
            self.fields['instructor_last_name'].initial = user.last_name
            self.fields['instructor_license_type'].initial = profile.instructor_license_type
            self.fields['instructor_license_number'].initial = user.national_id
        
        # Set default simulator to FPT if no initial value is provided
        if not self.initial.get('simulator'):
            try:
                default_simulator = Simulator.objects.filter(is_active=True, name='FPT').first()
                if default_simulator:
                    self.initial['simulator'] = default_simulator
            except:
                pass  # If FPT doesn't exist, just use the first available simulator

    def save(self, commit=True):
        """Override the save method to copy user_id to user_license_number and create SimEvaluation."""
        if not commit:
            # If not committing, just return the instance without saving
            instance = super().save(commit=False)
            instance.student_license_number = instance.student_id
            return instance
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            # First save the evaluation
            instance = super().save(commit=False)
            instance.student_license_number = instance.student_id
            instance.save()

            # Update student's accumulated hours LAST (after everything else succeeds)
            student_id = self.cleaned_data.get('student_id')
            session_sim_hours = self.cleaned_data.get('session_sim_hours')
            
            if student_id and session_sim_hours:
                student_profile = StudentProfile.objects.get(user__national_id=student_id)
                student_profile.sim_hours += session_sim_hours

                # Get the simulator object directly from cleaned_data (it's already a Simulator instance)
                sim = self.cleaned_data.get('simulator')
                session_type = self.cleaned_data.get('session_type')
                if session_type == 'Simple':
                    student_profile.balance -= round(session_sim_hours*sim.hourly_rate_single, 2)
                elif session_type == 'Dual':
                    student_profile.balance -= round(session_sim_hours*sim.hourly_rate_dual, 2)
                else:
                    student_profile.balance -= round(session_sim_hours*sim.hourly_rate_single, 2)
                student_profile.save()

                # Add session hours to simulator's total hours
                sim.total_hours += session_sim_hours
                sim.save()

        return instance

    def clean(self):
        cleaned_data = super().clean()
        student_id = cleaned_data.get('student_id')
        session_sim_hours = cleaned_data.get('session_sim_hours')
        
        # Validate session hours limit
        if session_sim_hours and session_sim_hours > 4.0:
            raise forms.ValidationError('Las horas de la sesión no pueden exceder 4 horas.')
        
        if student_id and session_sim_hours:
            try:
                student_profile = StudentProfile.objects.get(user__national_id=student_id)
                new_total = student_profile.sim_hours + session_sim_hours
                
                if new_total < 0:
                    raise forms.ValidationError(
                        f"Las horas acumuladas no pueden ser negativas. "
                        f"Horas actuales: {student_profile.sim_hours}, "
                        f"Horas de sesión: {session_sim_hours}, "
                        f"Total resultante: {new_total}"
                    )
            except StudentProfile.DoesNotExist:
                raise forms.ValidationError(f"No se encontró un perfil de estudiante con ID: {student_id}")
        
        return cleaned_data

class FlightEvaluation0_100Form(forms.ModelForm):
    # Add a custom aircraft field that uses ModelChoiceField
    aircraft = forms.ModelChoiceField(
        queryset=Aircraft.objects.filter(is_active=True),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-field'}),
        label='Aeronave'
    )
    
    class Meta:
        model = FlightEvaluation0_100
        fields = [
            'instructor_id', 'instructor_first_name', 'instructor_last_name',
            'instructor_license_type', 'instructor_license_number',
            'student_id', 'student_first_name', 'student_last_name',
            'student_license_type', 'course_type',
            'flight_rules', 'solo_flight', 'session_number', 'session_letter', 'session_date',
            'accumulated_flight_hours', 'initial_hourmeter', 'final_hourmeter', 'fuel_consumed', 'aircraft', 'session_grade',
            'pre_1', 'pre_2', 'pre_3', 'pre_4', 'pre_5', 'pre_6',
            'to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6',
            'mvrs_1', 'mvrs_2', 'mvrs_3', 'mvrs_4', 'mvrs_5', 'mvrs_6', 'mvrs_7', 'mvrs_8',
            'mvrs_9', 'mvrs_10', 'mvrs_11', 'mvrs_12', 'mvrs_13', 'mvrs_14', 'mvrs_15', 'mvrs_16', 'mvrs_17', 'mvrs_18',
            'nav_1', 'nav_2', 'nav_3', 'nav_4', 'nav_5', 'nav_6',
            'land_1', 'land_2', 'land_3', 'land_4', 'land_5', 'land_6', 'land_7', 'land_8', 'land_9', 'land_10',
            'emer_1', 'emer_2', 'emer_3', 'emer_4', 'emer_5', 'emer_6',
            'gen_1', 'gen_2', 'gen_3', 'gen_4', 'gen_5', 'gen_6', 'gen_7',
            'comments',
        ]

        labels = {
            'instructor_id': 'Número de cédula',
            'instructor_first_name': 'Nombre',
            'instructor_last_name': 'Apellido',
            'instructor_license_type': 'Tipo de licencia',
            'instructor_license_number': 'Número de licencia',
            'student_id': 'Número de cédula',
            'student_first_name': 'Nombre',
            'student_last_name': 'Apellido',
            'student_license_type': 'Tipo de licencia',
            'course_type': 'Curso',
            'flight_rules': 'Reglas de vuelo',
            'solo_flight': 'Vuelo solo',
            'session_number': 'Número de sesión',
            'session_letter': 'Repetición de la sesión',
            'session_date': 'Fecha de la sesión',
            'accumulated_flight_hours': 'Horas de vuelo acumuladas',
            'initial_hourmeter': 'Horómetro inicial',
            'final_hourmeter': 'Horómetro final',
            'fuel_consumed': 'Combustible consumido (litros)',
            'aircraft': 'Aeronave',
            'session_grade': 'Calificación de la sesión',
            'pre_1': 'Plan de vuelo VFR',
            'pre_2': 'Inspección pre-vuelo',
            'pre_3': 'Uso correcto de checklist',
            'pre_4': 'Comunicaciones aeronáuticas',
            'pre_5': 'Técnica de rodaje',
            'pre_6': 'Anormalidades en el encendido y taxeo',
            'to_1': 'Normal/Estático/Rolling',
            'to_2': 'Viento cruzado',
            'to_3': 'Pista corta y/o campo blando',
            'to_4': 'Ascenso (potencia/velocidad/rumbo)',
            'to_5': 'Comunicaciones aeronáuticas',
            'to_6': 'Ejecución salida visual',
            'mvrs_1': 'Uso de compensadores',
            'mvrs_2': 'Técnica de nivelado (control y comportamiento)',
            'mvrs_3': 'Vuelto recto nivelado',
            'mvrs_4': 'Virajes de 10, 20, 30 y 45',
            'mvrs_5': 'Virajes ascenso/descenso',
            'mvrs_6': 'Vuelo lento',
            'mvrs_7': 'Pérdida limpia',
            'mvrs_8': 'Pérdida config. despegue y aterrizaje',
            'mvrs_9': 'Pérdida secundaria',
            'mvrs_10': 'Efecto del P-factor',
            'mvrs_11': 'Chandelles',
            'mvrs_12': '8 perezosos',
            'mvrs_13': 'S sobre pilones',
            'mvrs_14': 'S sobre carreteras',
            'mvrs_15': 'Descenso c/s potencia (glide speed)',
            'mvrs_16': 'Ubicación espacial',
            'mvrs_17': 'Reconocimiento de actitud inusual (UPSET)',
            'mvrs_18': 'Precisión de 090, 180, 360 y 720',
            'nav_1': 'Briefing de pre-vuelo',
            'nav_2': 'Planificación/Tablas de performance',
            'nav_3': 'Plan de vuelo operacional (TOC-TOD)',
            'nav_4': 'Comunicaciones en ruta (reportes)',
            'nav_5': 'Orientación espacial',
            'nav_6': 'Uso de radioayudas',
            'land_1': 'Comunicación',
            'land_2': 'Procedimiento de circuito',
            'land_3': 'Maniobra de derrape (demo)',
            'land_4': 'Configuración de aterrizaje (limpio/full flaps)',
            'land_5': 'Aproximación estabilizada',
            'land_6': 'Aterrizaje normal',
            'land_7': 'Aterrizaje corto/campo suave',
            'land_8': 'Toque y despegue',
            'land_9': 'Go-around',
            'land_10': 'Situaciones anormales en el circuito',
            'emer_1': 'Actitud y juicio',
            'emer_2': 'Identificación de la anormalidad',
            'emer_3': 'Procedimientos memory-items y anormales',
            'emer_4': 'Control de la aeronave',
            'emer_5': 'Navegación (plan alterno en ruta)',
            'emer_6': 'Comunicaciones',
            'gen_1': 'Actitud y criterio',
            'gen_2': 'Seguridad de vuelo',
            'gen_3': 'Disciplina de vuelo',
            'gen_4': 'Técnica de vuelo',
            'gen_5': 'Conocimiento de la aeronave y limitaciones',
            'gen_6': 'Conocimiento RAV',
            'gen_7': 'Juicio general',
            'comments': '',
        }

        widgets = {
            'instructor_id': forms.NumberInput(attrs={'class': 'form-field'}),
            'instructor_first_name': forms.TextInput(attrs={'class': 'form-field'}),
            'instructor_last_name': forms.TextInput(attrs={'class': 'form-field'}),
            'instructor_license_type': forms.Select(attrs={'class': 'form-field'}),
            'instructor_license_number': forms.NumberInput(attrs={'class': 'form-field'}),
            'student_id': forms.NumberInput(attrs={'class': 'form-field'}),
            'student_first_name': forms.TextInput(attrs={'class': 'form-field'}),
            'student_last_name': forms.TextInput(attrs={'class': 'form-field'}),
            'student_license_type': forms.Select(attrs={'class': 'form-field'}),
            'course_type': forms.Select(attrs={'class': 'form-field'}),
            'flight_rules': forms.Select(attrs={'class': 'form-field'}),
            'solo_flight': forms.Select(attrs={'class': 'form-field'}),
            'session_number': forms.Select(attrs={'class': 'form-field'}),
            'session_letter': forms.Select(attrs={'class': 'form-field'}),
            'session_date': forms.DateInput(attrs={'class': 'form-field', 'type': 'date'}),
            'accumulated_flight_hours': forms.TextInput(attrs={'class': 'form-field disabled-field', 'readonly': 'readonly'}),
            'initial_hourmeter': forms.NumberInput(attrs={'class': 'form-field'}),
            'final_hourmeter': forms.NumberInput(attrs={'class': 'form-field'}),
            'fuel_consumed': forms.NumberInput(attrs={'class': 'form-field'}),
            'aircraft': forms.Select(attrs={'class': 'form-field'}),
            'session_grade': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_7': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_8': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_9': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_10': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_11': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_12': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_13': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_14': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_15': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_16': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_17': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'mvrs_18': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'nav_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'nav_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'nav_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'nav_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'nav_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'nav_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_7': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_8': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_9': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_10': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'emer_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'emer_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'emer_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'emer_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'emer_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'emer_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_7': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'comments': forms.Textarea(attrs={'class': 'form-field', 'rows': 10, 'placeholder': 'Mínimo 75 caracteres, máximo 1000 caracteres'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extract the 'user' argument from kwargs
        super().__init__(*args, **kwargs)
        
        # Set student fields to empty to prevent preselection
        self.fields['student_license_type'].initial = ''
        self.fields['course_type'].initial = ''
        
        # Override the field choices to include empty option
        self.fields['student_license_type'].choices = [('', '---------')] + list(self.fields['student_license_type'].choices)
        self.fields['course_type'].choices = [('', '---------')] + list(self.fields['course_type'].choices)
        
        if user:
            profile = user.instructor_profile
            self.fields['instructor_id'].initial = user.national_id
            self.fields['instructor_first_name'].initial = user.first_name
            self.fields['instructor_last_name'].initial = user.last_name
            self.fields['instructor_license_type'].initial = profile.instructor_license_type
            self.fields['instructor_license_number'].initial = user.national_id

    def save(self, commit=True):
        """Override the save method to copy user_id to user_license_number and create FlightEvaluation0_100."""
        if not commit:
            # If not committing, just return the instance without saving
            instance = super().save(commit=False)
            instance.student_license_number = instance.student_id
            return instance
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            # First save the evaluation
            instance = super().save(commit=False)
            instance.student_license_number = instance.student_id
            instance.save()

            # Update student's accumulated hours LAST (after everything else succeeds)
            student_id = self.cleaned_data.get('student_id')
            session_flight_hours = self.cleaned_data.get('session_flight_hours')
            aircraft = self.cleaned_data.get('aircraft')
            fuel_consumed = self.cleaned_data.get('fuel_consumed')
            fuel_cost = aircraft.fuel_cost

            if student_id and session_flight_hours:
                student_profile = StudentProfile.objects.get(user__national_id=student_id)
                # Update student's accumulated flight hours and flight balance
                student_profile.flight_hours += session_flight_hours

                if student_profile.flight_rate != 130.0:
                    hourly_rate = student_profile.flight_rate
                else:
                    hourly_rate = aircraft.hourly_rate

                student_profile.balance -= round(session_flight_hours*hourly_rate + fuel_cost*fuel_consumed, 2)
                student_profile.save()
                # Update aircraft's total hours
                aircraft.total_hours += session_flight_hours
                aircraft.save()

        return instance
    
    def clean(self):
        cleaned_data = super().clean()
        student_id = cleaned_data.get('student_id')
        initial_hourmeter = cleaned_data.get('initial_hourmeter')
        final_hourmeter = cleaned_data.get('final_hourmeter')
        aircraft = cleaned_data.get('aircraft')
        
        if initial_hourmeter and final_hourmeter:
            calculated_session_flight_hours = round(final_hourmeter - initial_hourmeter, 1)
            # Add 40% to the flight hours for the YV206E only.
            if aircraft.registration == 'YV206E':
                calculated_session_flight_hours = round(calculated_session_flight_hours * decimal.Decimal('1.4'), 1)
            if calculated_session_flight_hours < 0:
                raise forms.ValidationError(
                    f"El horómetro final no puede ser menor que el horómetro inicial. "
                    f"Horómetro inicial: {initial_hourmeter}, "
                    f"Horómetro final: {final_hourmeter}"
                )
            if calculated_session_flight_hours > 14.0:
                raise forms.ValidationError(
                    f"Las horas de la sesión no pueden exceder 14 horas. "
                    f"Horas de sesión: {calculated_session_flight_hours}"
                )
        else:
            raise forms.ValidationError(
                f"El horómetro inicial y el horómetro final son requeridos. "
                f"Horómetro inicial: {initial_hourmeter}, "
                f"Horómetro final: {final_hourmeter}"
            )
        cleaned_data['session_flight_hours'] = calculated_session_flight_hours

        if student_id and calculated_session_flight_hours:
            try:
                student_profile = StudentProfile.objects.get(user__national_id=student_id)
                new_total = student_profile.flight_hours + calculated_session_flight_hours
                
                if new_total < 0:
                    raise forms.ValidationError(
                        f"Las horas acumuladas no pueden ser negativas. "
                        f"Horas actuales: {student_profile.flight_hours}, "
                        f"Horas de sesión: {calculated_session_flight_hours}, "
                        f"Total resultante: {new_total}"
                    )
            except StudentProfile.DoesNotExist:
                raise forms.ValidationError(f"No se encontró un perfil de estudiante con ID: {student_id}")
        
        return cleaned_data

class FlightEvaluation100_120Form(forms.ModelForm):
    # Add a custom aircraft field that uses ModelChoiceField
    aircraft = forms.ModelChoiceField(
        queryset=Aircraft.objects.filter(is_active=True),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-field'}),
        label='Aeronave'
    )
    
    class Meta:
        model = FlightEvaluation100_120
        fields = [
            'instructor_id', 'instructor_first_name', 'instructor_last_name',
            'instructor_license_type', 'instructor_license_number',
            'student_id', 'student_first_name', 'student_last_name',
            'student_license_type', 'course_type',
            'flight_rules', 'solo_flight', 'session_number', 'session_letter', 'session_date',
            'accumulated_flight_hours', 'initial_hourmeter', 'final_hourmeter', 'fuel_consumed', 'aircraft', 'session_grade',
            'pre_1', 'pre_2', 'pre_3', 'pre_4', 'pre_5', 'pre_6',
            'to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6',
            'b_ifr_1', 'b_ifr_2', 'b_ifr_3', 'b_ifr_4', 'b_ifr_5', 'b_ifr_6', 'b_ifr_7', 'b_ifr_8', 'b_ifr_9', 'b_ifr_10', 'b_ifr_11',
            'a_ifr_1', 'a_ifr_2', 'a_ifr_3', 'a_ifr_4', 'a_ifr_5', 'a_ifr_6', 'a_ifr_7', 'a_ifr_8', 'a_ifr_9', 'a_ifr_10', 'a_ifr_11',
            'land_1', 'land_2', 'land_3', 'land_4', 'land_5', 'land_6', 'land_7',
            'emer_1', 'emer_2', 'emer_3', 'emer_4', 'emer_5',
            'gen_1', 'gen_2', 'gen_3', 'gen_4', 'gen_5', 'gen_6', 'gen_7',
            'comments',
        ]

        labels = {
            'instructor_id': 'Número de cédula',
            'instructor_first_name': 'Nombre',
            'instructor_last_name': 'Apellido',
            'instructor_license_type': 'Tipo de licencia',
            'instructor_license_number': 'Número de licencia',
            'student_id': 'Número de cédula',
            'student_first_name': 'Nombre',
            'student_last_name': 'Apellido',
            'student_license_type': 'Tipo de licencia',
            'course_type': 'Curso',
            'flight_rules': 'Reglas de vuelo',
            'solo_flight': 'Vuelo solo',
            'session_number': 'Número de sesión',
            'session_letter': 'Repetición de la sesión',
            'session_date': 'Fecha de la sesión',
            'accumulated_flight_hours': 'Horas de vuelo acumuladas',
            'initial_hourmeter': 'Horómetro inicial',
            'final_hourmeter': 'Horómetro final',
            'fuel_consumed': 'Combustible consumido (litros)',
            'aircraft': 'Aeronave',
            'session_grade': 'Calificación de la sesión',
            'pre_1': 'Plan de vuelo IFR',
            'pre_2': 'Inspección pre-vuelo',
            'pre_3': 'Uso correcto de checklist',
            'pre_4': 'Comunicaciones aeronáuticas',
            'pre_5': 'Técnica de rodaje',
            'pre_6': 'Anormalidades en el encendido y taxeo',
            'to_1': 'Normal',
            'to_2': 'Viento cruzado',
            'to_3': 'Pista corta',
            'to_4': 'Ascenso (potencia/velocidad/rumbo)',
            'to_5': 'Comunicaciones aeronáuticas IFR',
            'to_6': 'Ejecución SID',
            'b_ifr_1': 'Maniobra tipo S (SA, SB, SC, SD)',
            'b_ifr_2': 'Virajes cronometrados (1 RST / 1/2 RST)',
            'b_ifr_3': 'Reconocimiento de actitud inusual (UPSET)',
            'b_ifr_4': 'Serie de virajes',
            'b_ifr_5': 'Cambios de velocidad',
            'b_ifr_6': 'Intercepción de radiales (IB/OB)',
            'b_ifr_7': 'Interceptación de marcaciones',
            'b_ifr_8': 'Uso de instrumentos de navegación (chequeos)',
            'b_ifr_9': 'Chequeo cruzado',
            'b_ifr_10': 'Virajes inversión curso (45x180) (80x260) (base)',
            'b_ifr_11': 'Patrón de juego',
            'a_ifr_1': 'Plan de vuelo/operacional (IFR)',
            'a_ifr_2': 'Planificación IFR',
            'a_ifr_3': 'Comunicaciones IFR (reportes)',
            'a_ifr_4': 'Ejecución SID',
            'a_ifr_5': 'Viraje de procedimiento (45x180) (base)',
            'a_ifr_6': 'Arcos/DME',
            'a_ifr_7': 'Procedimientos de no-precisión',
            'a_ifr_8': 'Procedimientos APV (demo)',
            'a_ifr_9': 'Procedimientos de precisión',
            'a_ifr_10': 'Procedimiento de aprox. frustrada',
            'a_ifr_11': 'Circuitos de espera',
            'land_1': 'Aterrizaje normal',
            'land_2': 'Aproximación estabilizada',
            'land_3': 'Aproximación frustrada',
            'land_4': 'Ejecución de procedimiento IFR',
            'land_5': 'Transición IFR a referencias visuales',
            'land_6': 'Disciplina de vuelo',
            'land_7': 'Técnica de vuelo',
            'emer_1': 'Actitud y juicio',
            'emer_2': 'Identificación de la anormalidad',
            'emer_3': 'Procedimientos memory-items y anormales',
            'emer_4': 'Recuperación de pérdida por instrumentos',
            'emer_5': 'Panel parcial',
            'gen_1': 'Actitud y criterio',
            'gen_2': 'Seguridad de vuelo',
            'gen_3': 'Disciplina de vuelo',
            'gen_4': 'Técnica de vuelo',
            'gen_5': 'Conocimiento de la aeronave y limitaciones',
            'gen_6': 'Conocimiento RAV',
            'gen_7': 'Juicio general',
            'comments': '',
        }

        widgets = {
            'instructor_id': forms.NumberInput(attrs={'class': 'form-field'}),
            'instructor_first_name': forms.TextInput(attrs={'class': 'form-field'}),
            'instructor_last_name': forms.TextInput(attrs={'class': 'form-field'}),
            'instructor_license_type': forms.Select(attrs={'class': 'form-field'}),
            'instructor_license_number': forms.NumberInput(attrs={'class': 'form-field'}),
            'student_id': forms.NumberInput(attrs={'class': 'form-field'}),
            'student_first_name': forms.TextInput(attrs={'class': 'form-field'}),
            'student_last_name': forms.TextInput(attrs={'class': 'form-field'}),
            'student_license_type': forms.Select(attrs={'class': 'form-field'}),
            'course_type': forms.Select(attrs={'class': 'form-field'}),
            'flight_rules': forms.Select(attrs={'class': 'form-field'}),
            'solo_flight': forms.Select(attrs={'class': 'form-field'}),
            'session_number': forms.Select(attrs={'class': 'form-field'}),
            'session_letter': forms.Select(attrs={'class': 'form-field'}),
            'session_date': forms.DateInput(attrs={'class': 'form-field', 'type': 'date'}),
            'accumulated_flight_hours': forms.TextInput(attrs={'class': 'form-field disabled-field', 'readonly': 'readonly'}),
            'aircraft': forms.Select(attrs={'class': 'form-field'}),
            'session_grade': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'b_ifr_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'b_ifr_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'b_ifr_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'b_ifr_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'b_ifr_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'b_ifr_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'b_ifr_7': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'b_ifr_8': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'b_ifr_9': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'b_ifr_10': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'b_ifr_11': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'a_ifr_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'a_ifr_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'a_ifr_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'a_ifr_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'a_ifr_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'a_ifr_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'a_ifr_7': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'a_ifr_8': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'a_ifr_9': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'a_ifr_10': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'a_ifr_11': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_7': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'emer_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'emer_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'emer_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'emer_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'emer_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_7': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'comments': forms.Textarea(attrs={'class': 'form-field', 'rows': 10, 'placeholder': 'Mínimo 75 caracteres, máximo 1000 caracteres'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extract the 'user' argument from kwargs
        super().__init__(*args, **kwargs)
        
        # Set student fields to empty to prevent preselection
        self.fields['student_license_type'].initial = ''
        self.fields['course_type'].initial = ''
        
        # Override the field choices to include empty option
        self.fields['student_license_type'].choices = [('', '---------')] + list(self.fields['student_license_type'].choices)
        self.fields['course_type'].choices = [('', '---------')] + list(self.fields['course_type'].choices)
        
        if user:
            profile = user.instructor_profile
            self.fields['instructor_id'].initial = user.national_id
            self.fields['instructor_first_name'].initial = user.first_name
            self.fields['instructor_last_name'].initial = user.last_name
            self.fields['instructor_license_type'].initial = profile.instructor_license_type
            self.fields['instructor_license_number'].initial = user.national_id

    def save(self, commit=True):
        """Override the save method to copy user_id to user_license_number and create FlightEvaluation100_120."""
        if not commit:
            # If not committing, just return the instance without saving
            instance = super().save(commit=False)
            instance.student_license_number = instance.student_id
            return instance
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            # First save the evaluation
            instance = super().save(commit=False)
            instance.student_license_number = instance.student_id
            instance.save()

            # Update student's accumulated hours LAST (after everything else succeeds)
            student_id = self.cleaned_data.get('student_id')
            session_flight_hours = self.cleaned_data.get('session_flight_hours')
            aircraft = self.cleaned_data.get('aircraft')
            fuel_consumed = self.cleaned_data.get('fuel_consumed')
            fuel_cost = aircraft.fuel_cost

            if student_id and session_flight_hours:
                student_profile = StudentProfile.objects.get(user__national_id=student_id)
                # Update student's accumulated flight hours and flight balance
                student_profile.flight_hours += session_flight_hours

                if student_profile.flight_rate != 130.0:
                    hourly_rate = student_profile.flight_rate
                else:
                    hourly_rate = aircraft.hourly_rate

                student_profile.balance -= round(session_flight_hours*aircraft.hourly_rate + fuel_cost*fuel_consumed, 2)
                student_profile.save()
                # Update aircraft's total hours
                aircraft.total_hours += session_flight_hours
                aircraft.save()

        return instance

    def clean(self):
        cleaned_data = super().clean()
        student_id = cleaned_data.get('student_id')
        initial_hourmeter = cleaned_data.get('initial_hourmeter')
        final_hourmeter = cleaned_data.get('final_hourmeter')
        aircraft = cleaned_data.get('aircraft')
        
        if initial_hourmeter and final_hourmeter:
            calculated_session_flight_hours = round(final_hourmeter - initial_hourmeter, 1)
            # Add 40% to the flight hours for the YV206E only.
            if aircraft.registration == 'YV206E':
                calculated_session_flight_hours = round(calculated_session_flight_hours * decimal.Decimal('1.4'), 1)
            if calculated_session_flight_hours < 0:
                raise forms.ValidationError(
                    f"El horómetro final no puede ser menor que el horómetro inicial. "
                    f"Horómetro inicial: {initial_hourmeter}, "
                    f"Horómetro final: {final_hourmeter}"
                )
            if calculated_session_flight_hours > 14.0:
                raise forms.ValidationError(
                    f"Las horas de la sesión no pueden exceder 14 horas. "
                    f"Horas de sesión: {calculated_session_flight_hours}"
                )
        else:
            raise forms.ValidationError(
                f"El horómetro inicial y el horómetro final son requeridos. "
                f"Horómetro inicial: {initial_hourmeter}, "
                f"Horómetro final: {final_hourmeter}"
            )
        cleaned_data['session_flight_hours'] = calculated_session_flight_hours
        
        if student_id and calculated_session_flight_hours:
            try:
                student_profile = StudentProfile.objects.get(user__national_id=student_id)
                new_total = student_profile.flight_hours + calculated_session_flight_hours
                
                if new_total < 0:
                    raise forms.ValidationError(
                        f"Las horas acumuladas no pueden ser negativas. "
                        f"Horas actuales: {student_profile.flight_hours}, "
                        f"Horas de sesión: {calculated_session_flight_hours}, "
                        f"Total resultante: {new_total}"
                    )
            except StudentProfile.DoesNotExist:
                raise forms.ValidationError(f"No se encontró un perfil de estudiante con ID: {student_id}")
        
        return cleaned_data

class FlightEvaluation120_170Form(forms.ModelForm):
    # Add a custom aircraft field that uses ModelChoiceField
    aircraft = forms.ModelChoiceField(
        queryset=Aircraft.objects.filter(is_active=True),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-field'}),
        label='Aeronave'
    )
    
    class Meta:
        model = FlightEvaluation120_170
        fields = [
            'instructor_id', 'instructor_first_name', 'instructor_last_name',
            'instructor_license_type', 'instructor_license_number',
            'student_id', 'student_first_name', 'student_last_name',
            'student_license_type', 'course_type',
            'flight_rules', 'solo_flight', 'session_number', 'session_letter', 'session_date',
            'accumulated_flight_hours', 'initial_hourmeter', 'final_hourmeter', 'fuel_consumed', 'aircraft', 'session_grade',
            'pre_1', 'pre_2', 'pre_3', 'pre_4', 'pre_5', 'pre_6',
            'to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6',
            'inst_1', 'inst_2', 'inst_3', 'inst_4', 'inst_5', 'inst_6', 'inst_7', 'inst_8', 'inst_9', 'inst_10', 'inst_11',
            'land_1', 'land_2', 'land_3', 'land_4', 'land_5', 'land_6', 'land_7',
            'emer_1', 'emer_2', 'emer_3', 'emer_4',
            'gen_1', 'gen_2', 'gen_3', 'gen_4', 'gen_5', 'gen_6', 'gen_7',
            'comments',
        ]

        labels = {
            'instructor_id': 'Número de cédula',
            'instructor_first_name': 'Nombre',
            'instructor_last_name': 'Apellido',
            'instructor_license_type': 'Tipo de licencia',
            'instructor_license_number': 'Número de licencia',
            'student_id': 'Número de cédula',
            'student_first_name': 'Nombre',
            'student_last_name': 'Apellido',
            'student_license_type': 'Tipo de licencia',
            'course_type': 'Curso',
            'flight_rules': 'Reglas de vuelo',
            'solo_flight': 'Vuelo solo',
            'session_number': 'Número de sesión',
            'session_letter': 'Repetición de la sesión',
            'session_date': 'Fecha de la sesión',
            'accumulated_flight_hours': 'Horas de vuelo acumuladas',    
            'initial_hourmeter': 'Horómetro inicial',
            'final_hourmeter': 'Horómetro final',
            'fuel_consumed': 'Combustible consumido (litros)',
            'aircraft': 'Aeronave',
            'session_grade': 'Calificación de la sesión',
            'pre_1': 'Plan de vuelo VFR/IFR',
            'pre_2': 'Insp. pre-vuelo/briefing (Serv/WX/NOTAMs)',
            'pre_3': 'Uso correcto de checklist',
            'pre_4': 'Comns. IFR (ICAO 4) (ATIS/Clearance)',
            'pre_5': 'Técnica de rodaje/hotspot/lectura taxi-route',
            'pre_6': 'Anormalidades en el encendido y taxeo',
            'to_1': 'Normal',
            'to_2': 'Viento cruzado',
            'to_3': 'Pista corta y/o suave',
            'to_4': 'Ascenso (potencia/velocidad/rumbo)',
            'to_5': 'Comunicación (ICAO 4)',
            'to_6': 'Ejecución SID (salidas vectorizadas)',
            'inst_1': 'Plan de vuelo/operacional (IFR)',
            'inst_2': 'Planificación IFR',
            'inst_3': 'Comns. IFR (ICAO 4) (ATIS/Clearance)',
            'inst_4': 'Radionavegación convencional/RNAV',
            'inst_5': 'Viraje de procedimiento (45x180) (base)',
            'inst_6': 'Arcos/DME',
            'inst_7': 'Procedimientos de no-precisión',
            'inst_8': 'Procedimientos APV (demo)',
            'inst_9': 'Procedimientos de precisión',
            'inst_10': 'Procedimiento de aprox. frustrada',
            'inst_11': 'Circuitos de espera',
            'land_1': 'Aterrizaje normal',
            'land_2': 'Aproximación estabilizada',
            'land_3': 'Aproximación frustrada',
            'land_4': 'Ejecución de procedimiento IFR',
            'land_5': 'Transición IFR a referencias visuales',
            'land_6': 'Procedimiento taxi out',
            'land_7': 'Técnica de vuelo',
            'emer_1': 'Windshear',
            'emer_2': 'Evento TCAS',
            'emer_3': 'Incapacitación del piloto',
            'emer_4': 'Sin radiocomunicaciones abordo (NORDO)',
            'gen_1': 'Actitud y criterio',
            'gen_2': 'Seguridad de vuelo',
            'gen_3': 'Disciplina de vuelo',
            'gen_4': 'Técnica de vuelo',
            'gen_5': 'Conocimiento de la aeronave y limitaciones',
            'gen_6': 'Conocimiento RAV',
            'gen_7': 'Juicio general',
            'comments': '',
        }

        widgets = {
            'instructor_id': forms.NumberInput(attrs={'class': 'form-field'}),
            'instructor_first_name': forms.TextInput(attrs={'class': 'form-field'}),
            'instructor_last_name': forms.TextInput(attrs={'class': 'form-field'}),
            'instructor_license_type': forms.Select(attrs={'class': 'form-field'}),
            'instructor_license_number': forms.NumberInput(attrs={'class': 'form-field'}),
            'student_id': forms.NumberInput(attrs={'class': 'form-field'}),
            'student_first_name': forms.TextInput(attrs={'class': 'form-field'}),
            'student_last_name': forms.TextInput(attrs={'class': 'form-field'}),
            'student_license_type': forms.Select(attrs={'class': 'form-field'}),
            'course_type': forms.Select(attrs={'class': 'form-field'}),
            'flight_rules': forms.Select(attrs={'class': 'form-field'}),
            'solo_flight': forms.Select(attrs={'class': 'form-field'}),
            'session_number': forms.Select(attrs={'class': 'form-field'}),
            'session_letter': forms.Select(attrs={'class': 'form-field'}),
            'session_date': forms.DateInput(attrs={'class': 'form-field', 'type': 'date'}),
            'accumulated_flight_hours': forms.TextInput(attrs={'class': 'form-field disabled-field', 'readonly': 'readonly'}),
            'aircraft': forms.Select(attrs={'class': 'form-field'}),
            'session_grade': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'pre_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'to_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_7': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_8': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_9': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_10': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'inst_11': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'land_7': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'emer_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'emer_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'emer_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'emer_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_1': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_2': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_3': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_4': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_5': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_6': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'gen_7': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'comments': forms.Textarea(attrs={'class': 'form-field', 'rows': 10, 'placeholder': 'Mínimo 75 caracteres, máximo 1000 caracteres'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extract the 'user' argument from kwargs
        super().__init__(*args, **kwargs)
        
        # Set student fields to empty to prevent preselection
        self.fields['student_license_type'].initial = ''
        self.fields['course_type'].initial = ''
        
        # Override the field choices to include empty option
        self.fields['student_license_type'].choices = [('', '---------')] + list(self.fields['student_license_type'].choices)
        self.fields['course_type'].choices = [('', '---------')] + list(self.fields['course_type'].choices)
        
        if user:
            profile = user.instructor_profile
            self.fields['instructor_id'].initial = user.national_id
            self.fields['instructor_first_name'].initial = user.first_name
            self.fields['instructor_last_name'].initial = user.last_name
            self.fields['instructor_license_type'].initial = profile.instructor_license_type
            self.fields['instructor_license_number'].initial = user.national_id

    def save(self, commit=True):
        """Override the save method to copy user_id to user_license_number and create FlightEvaluation120_170."""
        if not commit:
            # If not committing, just return the instance without saving
            instance = super().save(commit=False)
            instance.student_license_number = instance.student_id
            return instance
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            # First save the evaluation
            instance = super().save(commit=False)
            instance.student_license_number = instance.student_id
            instance.save()

            # Update student's accumulated hours LAST (after everything else succeeds)
            student_id = self.cleaned_data.get('student_id')
            session_flight_hours = self.cleaned_data.get('session_flight_hours')
            aircraft = self.cleaned_data.get('aircraft')
            fuel_consumed = self.cleaned_data.get('fuel_consumed')
            fuel_cost = aircraft.fuel_cost

            if student_id and session_flight_hours:
                student_profile = StudentProfile.objects.get(user__national_id=student_id)
                # Update student's accumulated flight hours and flight balance
                student_profile.flight_hours += session_flight_hours

                if student_profile.flight_rate != 130.0:
                    hourly_rate = student_profile.flight_rate
                else:
                    hourly_rate = aircraft.hourly_rate

                student_profile.balance -= round(session_flight_hours*hourly_rate + fuel_cost*fuel_consumed, 2)
                student_profile.save()
                # Update aircraft's total hours
                aircraft.total_hours += session_flight_hours
                aircraft.save()

        return instance
    
    def clean(self):
        cleaned_data = super().clean()
        student_id = cleaned_data.get('student_id')
        initial_hourmeter = cleaned_data.get('initial_hourmeter')
        final_hourmeter = cleaned_data.get('final_hourmeter')
        aircraft = cleaned_data.get('aircraft')
        
        if initial_hourmeter and final_hourmeter:
            calculated_session_flight_hours = round(final_hourmeter - initial_hourmeter, 1)
            # Add 40% to the flight hours for the YV206E only.
            if aircraft.registration == 'YV206E':
                calculated_session_flight_hours = round(calculated_session_flight_hours * decimal.Decimal('1.4'), 1)
            if calculated_session_flight_hours < 0:
                raise forms.ValidationError(
                    f"El horómetro final no puede ser menor que el horómetro inicial. "
                    f"Horómetro inicial: {initial_hourmeter}, "
                    f"Horómetro final: {final_hourmeter}"
                )
            if calculated_session_flight_hours > 14.0:
                raise forms.ValidationError(
                    f"Las horas de la sesión no pueden exceder 14 horas. "
                    f"Horas de sesión: {calculated_session_flight_hours}"
                )
        else:
            raise forms.ValidationError(
                f"El horómetro inicial y el horómetro final son requeridos. "
                f"Horómetro inicial: {initial_hourmeter}, "
                f"Horómetro final: {final_hourmeter}"
            )
        cleaned_data['session_flight_hours'] = calculated_session_flight_hours
        
        if student_id and calculated_session_flight_hours:
            try:
                student_profile = StudentProfile.objects.get(user__national_id=student_id)
                new_total = student_profile.flight_hours + calculated_session_flight_hours
                
                if new_total < 0:
                    raise forms.ValidationError(
                        f"Las horas acumuladas no pueden ser negativas. "
                        f"Horas actuales: {student_profile.flight_hours}, "
                        f"Horas de sesión: {calculated_session_flight_hours}, "
                        f"Total resultante: {new_total}"
                    )
            except StudentProfile.DoesNotExist:
                raise forms.ValidationError(f"No se encontró un perfil de estudiante con ID: {student_id}")
        
        return cleaned_data
    
class FlightReportForm(forms.ModelForm):
    # Add a custom aircraft field that uses ModelChoiceField
    aircraft = forms.ModelChoiceField(
        queryset=Aircraft.objects.filter(is_active=True),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-field'}),
        label='Aeronave'
    )
    
    class Meta:
        model = FlightReport
        fields = [
            'pilot_id', 'pilot_first_name', 'pilot_last_name',
            'pilot_license_number', 'flight_date', 'flight_reason',
            'initial_hourmeter', 'final_hourmeter', 'fuel_consumed', 'aircraft',
            'comments',
        ]

        labels = {
            'pilot_id': 'Número de cédula',
            'pilot_first_name': 'Nombre',
            'pilot_last_name': 'Apellido',
            'pilot_license_number': 'Número de licencia',
            'flight_date': 'Fecha',
            'flight_reason': 'Motivo',
            'initial_hourmeter': 'Horómetro inicial',
            'final_hourmeter': 'Horómetro final',
            'fuel_consumed': 'Combustible consumido (litros)',
            'aircraft': 'Aeronave',
            'comments': '',
        }

        widgets = {
            'pilot_id': forms.NumberInput(attrs={'class': 'form-field'}),
            'pilot_first_name': forms.TextInput(attrs={'class': 'form-field'}),
            'pilot_last_name': forms.TextInput(attrs={'class': 'form-field'}),
            'pilot_license_number': forms.NumberInput(attrs={'class': 'form-field'}),
            'flight_date': forms.DateInput(attrs={'class': 'form-field', 'type': 'date'}),
            'flight_reason': forms.Select(attrs={'class': 'form-field'}),
            'initial_hourmeter': forms.NumberInput(attrs={'class': 'form-field'}),
            'final_hourmeter': forms.NumberInput(attrs={'class': 'form-field'}),
            'fuel_consumed': forms.NumberInput(attrs={'class': 'form-field'}),
            'aircraft': forms.Select(attrs={'class': 'form-field'}),
            'comments': forms.Textarea(attrs={'class': 'form-field', 'rows': 10, 'placeholder': 'Máximo 1000 caracteres'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extract the 'user' argument from kwargs
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['pilot_id'].initial = user.national_id
            self.fields['pilot_first_name'].initial = user.first_name
            self.fields['pilot_last_name'].initial = user.last_name
            self.fields['pilot_license_number'].initial = user.national_id

    def save(self, commit=True):
        """Override the save method to copy user_id to user_license_number and create FlightReport."""
        if not commit:
            # If not committing, just return the instance without saving
            instance = super().save(commit=False)
            instance.pilot_license_number = instance.pilot_id
            return instance
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            # First save the report
            instance = super().save(commit=False)
            instance.pilot_license_number = instance.pilot_id
            instance.save()

            # Update aircraft's total hours.
            flight_hours = self.cleaned_data.get('flight_hours')
            aircraft = self.cleaned_data.get('aircraft')

            if flight_hours:
                # Update aircraft's total hours
                aircraft.total_hours += flight_hours
                aircraft.save()

        return instance

    def clean(self):
        cleaned_data = super().clean()
        initial_hourmeter = cleaned_data.get('initial_hourmeter')
        final_hourmeter = cleaned_data.get('final_hourmeter')
        
        if initial_hourmeter and final_hourmeter:
            calculated_flight_hours = round(final_hourmeter - initial_hourmeter, 1)
            if calculated_flight_hours < 0:
                raise forms.ValidationError(
                    f"El horómetro final no puede ser menor que el horómetro inicial. "
                    f"Horómetro inicial: {initial_hourmeter}, "
                    f"Horómetro final: {final_hourmeter}"
                )
            if calculated_flight_hours > 10.0:
                raise forms.ValidationError(
                    f"Las horas de la sesión no pueden exceder 10 horas. "
                    f"Horas de sesión: {calculated_flight_hours}"
                )
        else:
            raise forms.ValidationError(
                f"El horómetro inicial y el horómetro final son requeridos. "
                f"Horómetro inicial: {initial_hourmeter}, "
                f"Horómetro final: {final_hourmeter}"
            )
        cleaned_data['flight_hours'] = calculated_flight_hours
    
        return cleaned_data