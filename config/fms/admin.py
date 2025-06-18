from django.contrib import admin
from .models import FlightEvaluation0_100, FlightEvaluation100_120, FlightEvaluation120_170, FlightLog

@admin.register(FlightEvaluation0_100)
class FlightEvaluation0_100Admin(admin.ModelAdmin):
    list_display = [
        'student_full_name', 'student_id',
        'instructor_full_name', 'instructor_id',
        'flight_date_only', 'aircraft_registration', 'session_number', 'session_flight_hours'
    ]
    list_filter = ['flight_date', 'aircraft_registration', 'instructor_license_number', 'session_grade', 'course_type']
    search_fields = ['student_first_name', 'student_last_name', 'instructor_first_name', 'instructor_last_name']
    date_hierarchy = 'flight_date'
    ordering = ['-flight_date']
    
    fieldsets = (
        ('Sección 1: Datos del instructor', {
            'fields': (
                'instructor_id', 'instructor_first_name', 'instructor_last_name',
                'instructor_license_type', 'instructor_license_number'
            )
        }),
        ('Sección 2: Datos del alumno', {
            'fields': (
                'student_id', 'student_first_name', 'student_last_name', 
                'student_license_type', 'student_license_number', 'course_type'
            )
        }),
        ('Sección 3: Datos de la sesión', {
            'fields': (
                'flight_rules', 'solo_flight', 'session_number', 
                'session_letter', 'accumulated_flight_hours', 'session_flight_hours',
                'aircraft_registration', 'session_grade'
            )
        }),
        ('Sección 4: Prevuelo / Encendido / Taxeo', {
            'fields': ('pre_1', 'pre_2', 'pre_3', 'pre_4', 'pre_5', 'pre_6'),
            'classes': ('collapse',)
        }),
        ('Sección 5: Despegue - Salida', {
            'fields': ('to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6'),
            'classes': ('collapse',)
        }),
        ('Sección 6: Maniobras', {
            'fields': (
                'mvrs_1', 'mvrs_2', 'mvrs_3', 'mvrs_4', 'mvrs_5', 'mvrs_6',
                'mvrs_7', 'mvrs_8', 'mvrs_9', 'mvrs_10', 'mvrs_11', 'mvrs_12',
                'mvrs_13', 'mvrs_14', 'mvrs_15', 'mvrs_16', 'mvrs_17', 'mvrs_18'
            ),
            'classes': ('collapse',)
        }),
        ('Sección 7: Emergencias', {
            'fields': ('emer_1', 'emer_2', 'emer_3', 'emer_4', 'emer_5', 'emer_6'),
            'classes': ('collapse',)
        }),
        ('Sección 8: Navegación VFR', {
            'fields': ('nav_1', 'nav_2', 'nav_3', 'nav_4', 'nav_5', 'nav_6'),
            'classes': ('collapse',)
        }),
        ('Sección 9: General', {
            'fields': ('gen_1', 'gen_2', 'gen_3', 'gen_4', 'gen_5', 'gen_6', 'gen_7'),
            'classes': ('collapse',)
        }),
        ('Sección 10: Circuito / Procedimiento', {
            'fields': (
                'land_1', 'land_2', 'land_3', 'land_4', 'land_5',
                'land_6', 'land_7', 'land_8', 'land_9', 'land_10'
            ),
            'classes': ('collapse',)
        }),
        ('Sección 11: Notas', {
            'fields': ('notes',)
        }),
    )
    
    readonly_fields = [
        'flight_date', 'instructor_id', 'instructor_first_name', 'instructor_last_name',
        'instructor_license_type', 'instructor_license_number', 'student_id', 'student_first_name',
        'student_last_name', 'student_license_type', 'student_license_number', 'course_type',
        'flight_rules', 'solo_flight', 'session_number', 'session_letter', 'accumulated_flight_hours',
        'session_flight_hours', 'aircraft_registration', 'session_grade', 'pre_1', 'pre_2', 'pre_3',
        'pre_4', 'pre_5', 'pre_6', 'to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6', 'mvrs_1', 'mvrs_2',
        'mvrs_3', 'mvrs_4', 'mvrs_5', 'mvrs_6', 'mvrs_7', 'mvrs_8', 'mvrs_9', 'mvrs_10', 'mvrs_11',
        'mvrs_12', 'mvrs_13', 'mvrs_14', 'mvrs_15', 'mvrs_16', 'mvrs_17', 'mvrs_18', 'emer_1', 'emer_2',
        'emer_3', 'emer_4', 'emer_5', 'emer_6', 'nav_1', 'nav_2', 'nav_3', 'nav_4', 'nav_5', 'nav_6',
        'gen_1', 'gen_2', 'gen_3', 'gen_4', 'gen_5', 'gen_6', 'gen_7', 'land_1', 'land_2', 'land_3',
        'land_4', 'land_5', 'land_6', 'land_7', 'land_8', 'land_9', 'land_10', 'notes'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def student_full_name(self, obj):
        return f"{obj.student_first_name} {obj.student_last_name}"
    student_full_name.short_description = 'Alumno'
    
    def instructor_full_name(self, obj):
        return f"{obj.instructor_first_name} {obj.instructor_last_name}"
    instructor_full_name.short_description = 'Instructor'
    
    def student_id(self, obj):
        return obj.student_license_number
    student_id.short_description = 'ID del alumno'
    
    def instructor_id(self, obj):
        return obj.instructor_license_number
    instructor_id.short_description = 'ID del instructor'
    
    def flight_date_only(self, obj):
        return obj.flight_date.date()
    flight_date_only.short_description = 'Fecha de vuelo'

    class Meta:
        verbose_name = 'Evaluación de vuelo 0-100'
        verbose_name_plural = 'Evaluaciones de vuelo 0-100'

@admin.register(FlightEvaluation100_120)
class FlightEvaluation100_120Admin(admin.ModelAdmin):
    list_display = [
        'student_full_name', 'student_id',
        'instructor_full_name', 'instructor_id',
        'flight_date_only', 'aircraft_registration', 'session_number', 'session_flight_hours'
    ]
    list_filter = ['flight_date', 'aircraft_registration', 'instructor_license_number', 'session_grade', 'course_type']
    search_fields = ['student_first_name', 'student_last_name', 'instructor_first_name', 'instructor_last_name']
    date_hierarchy = 'flight_date'
    ordering = ['-flight_date']
    
    fieldsets = (
        ('Sección 1: Datos del alumno', {
            'fields': (
                'student_id', 'student_first_name', 'student_last_name', 
                'student_license_type', 'student_license_number', 'course_type'
            )
        }),
        ('Sección 2: Datos del instructor', {
            'fields': (
                'instructor_id', 'instructor_first_name', 'instructor_last_name',
                'instructor_license_type', 'instructor_license_number'
            )
        }),
        ('Sección 3: Datos de la sesión', {
            'fields': (
                'flight_rules', 'solo_flight', 'session_number', 
                'session_letter', 'accumulated_flight_hours', 'session_flight_hours',
                'aircraft_registration', 'session_grade'
            )
        }),
        ('Sección 4: Prevuelo / Encendido / Taxeo', {
            'fields': ('pre_1', 'pre_2', 'pre_3', 'pre_4', 'pre_5', 'pre_6'),
            'classes': ('collapse',)
        }),
        ('Sección 5: Despegue - Salida instrumental', {
            'fields': ('to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6'),
            'classes': ('collapse',)
        }),
        ('Sección 6: Procedimientos IFR básicos', {
            'fields': (
                'b_ifr_1', 'b_ifr_2', 'b_ifr_3', 'b_ifr_4', 'b_ifr_5', 'b_ifr_6',
                'b_ifr_7', 'b_ifr_8', 'b_ifr_9', 'b_ifr_10', 'b_ifr_11'
            ),
            'classes': ('collapse',)
        }),
        ('Sección 7: Procedimientos IFR avanzados', {
            'fields': (
                'a_ifr_1', 'a_ifr_2', 'a_ifr_3', 'a_ifr_4', 'a_ifr_5', 'a_ifr_6',
                'a_ifr_7', 'a_ifr_8', 'a_ifr_9', 'a_ifr_10', 'a_ifr_11'
            ),
            'classes': ('collapse',)
        }),
        ('Sección 8: Aproximación final y aterrizaje', {
            'fields': ('land_1', 'land_2', 'land_3', 'land_4', 'land_5', 'land_6', 'land_7'),
            'classes': ('collapse',)
        }),
        ('Sección 9: Emergencias', {
            'fields': ('emer_1', 'emer_2', 'emer_3', 'emer_4', 'emer_5'),
            'classes': ('collapse',)
        }),
        ('Sección 10: General', {
            'fields': ('gen_1', 'gen_2', 'gen_3', 'gen_4', 'gen_5', 'gen_6', 'gen_7'),
            'classes': ('collapse',)
        }),
        ('Sección 11: Notas', {
            'fields': ('notes',)
        }),
    )
    
    readonly_fields = [
        'flight_date', 'student_id', 'student_first_name', 'student_last_name',
        'student_license_type', 'student_license_number', 'course_type', 'instructor_id',
        'instructor_first_name', 'instructor_last_name', 'instructor_license_type',
        'instructor_license_number', 'flight_rules', 'solo_flight', 'session_number',
        'session_letter', 'accumulated_flight_hours', 'session_flight_hours',
        'aircraft_registration', 'session_grade', 'pre_1', 'pre_2', 'pre_3', 'pre_4',
        'pre_5', 'pre_6', 'to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6', 'b_ifr_1',
        'b_ifr_2', 'b_ifr_3', 'b_ifr_4', 'b_ifr_5', 'b_ifr_6', 'b_ifr_7', 'b_ifr_8',
        'b_ifr_9', 'b_ifr_10', 'b_ifr_11', 'a_ifr_1', 'a_ifr_2', 'a_ifr_3', 'a_ifr_4',
        'a_ifr_5', 'a_ifr_6', 'a_ifr_7', 'a_ifr_8', 'a_ifr_9', 'a_ifr_10', 'a_ifr_11',
        'land_1', 'land_2', 'land_3', 'land_4', 'land_5', 'land_6', 'land_7', 'emer_1',
        'emer_2', 'emer_3', 'emer_4', 'emer_5', 'gen_1', 'gen_2', 'gen_3', 'gen_4',
        'gen_5', 'gen_6', 'gen_7', 'notes'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def student_full_name(self, obj):
        return f"{obj.student_first_name} {obj.student_last_name}"
    student_full_name.short_description = 'Alumno'
    
    def instructor_full_name(self, obj):
        return f"{obj.instructor_first_name} {obj.instructor_last_name}"
    instructor_full_name.short_description = 'Instructor'
    
    def student_id(self, obj):
        return obj.student_license_number
    student_id.short_description = 'ID del alumno'
    
    def instructor_id(self, obj):
        return obj.instructor_license_number
    instructor_id.short_description = 'ID del instructor'
    
    def flight_date_only(self, obj):
        return obj.flight_date.date()
    flight_date_only.short_description = 'Fecha de vuelo'

    class Meta:
        verbose_name = 'Evaluación de vuelo 100-120'
        verbose_name_plural = 'Evaluaciones de vuelo 100-120'

@admin.register(FlightEvaluation120_170)
class FlightEvaluation120_170Admin(admin.ModelAdmin):
    list_display = [
        'student_full_name', 'student_id',
        'instructor_full_name', 'instructor_id',
        'flight_date_only', 'aircraft_registration', 'session_number', 'session_flight_hours'
    ]
    list_filter = ['flight_date', 'aircraft_registration', 'instructor_license_number', 'session_grade', 'course_type']
    search_fields = ['student_first_name', 'student_last_name', 'instructor_first_name', 'instructor_last_name']
    date_hierarchy = 'flight_date'
    ordering = ['-flight_date']
    
    fieldsets = (
        ('Sección 1: Datos del alumno', {
            'fields': (
                'student_id', 'student_first_name', 'student_last_name', 
                'student_license_type', 'student_license_number', 'course_type'
            )
        }),
        ('Sección 2: Datos del instructor', {
            'fields': (
                'instructor_id', 'instructor_first_name', 'instructor_last_name',
                'instructor_license_type', 'instructor_license_number'
            )
        }),
        ('Sección 3: Datos de la sesión', {
            'fields': (
                'flight_rules', 'solo_flight', 'session_number', 
                'session_letter', 'accumulated_flight_hours', 'session_flight_hours',
                'aircraft_registration', 'session_grade'
            )
        }),
        ('Sección 4: Prevuelo / Encendido / Taxeo', {
            'fields': ('pre_1', 'pre_2', 'pre_3', 'pre_4', 'pre_5', 'pre_6'),
            'classes': ('collapse',)
        }),
        ('Sección 5: Despegue - Salida VFR/IFR', {
            'fields': ('to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6'),
            'classes': ('collapse',)
        }),
        ('Sección 6: Procedimientos IFR avanzados', {
            'fields': (
                'inst_1', 'inst_2', 'inst_3', 'inst_4', 'inst_5', 'inst_6',
                'inst_7', 'inst_8', 'inst_9', 'inst_10', 'inst_11'
            ),
            'classes': ('collapse',)
        }),
        ('Sección 7: Aproximación final y aterrizaje', {
            'fields': ('land_1', 'land_2', 'land_3', 'land_4', 'land_5', 'land_6', 'land_7'),
            'classes': ('collapse',)
        }),
        ('Sección 8: Emergencias situacionales', {
            'fields': ('emer_1', 'emer_2', 'emer_3', 'emer_4'),
            'classes': ('collapse',)
        }),
        ('Sección 9: General', {
            'fields': ('gen_1', 'gen_2', 'gen_3', 'gen_4', 'gen_5', 'gen_6', 'gen_7'),
            'classes': ('collapse',)
        }),
        ('Sección 10: Notas', {
            'fields': ('notes',)
        }),
    )
    
    readonly_fields = [
        'flight_date', 'student_id', 'student_first_name', 'student_last_name',
        'student_license_type', 'student_license_number', 'course_type', 'instructor_id',
        'instructor_first_name', 'instructor_last_name', 'instructor_license_type',
        'instructor_license_number', 'flight_rules', 'solo_flight', 'session_number',
        'session_letter', 'accumulated_flight_hours', 'session_flight_hours',
        'aircraft_registration', 'session_grade', 'pre_1', 'pre_2', 'pre_3', 'pre_4',
        'pre_5', 'pre_6', 'to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6', 'inst_1',
        'inst_2', 'inst_3', 'inst_4', 'inst_5', 'inst_6', 'inst_7', 'inst_8', 'inst_9',
        'inst_10', 'inst_11', 'land_1', 'land_2', 'land_3', 'land_4', 'land_5', 'land_6',
        'land_7', 'emer_1', 'emer_2', 'emer_3', 'emer_4', 'gen_1', 'gen_2', 'gen_3',
        'gen_4', 'gen_5', 'gen_6', 'gen_7', 'notes'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def student_full_name(self, obj):
        return f"{obj.student_first_name} {obj.student_last_name}"
    student_full_name.short_description = 'Alumno'
    
    def instructor_full_name(self, obj):
        return f"{obj.instructor_first_name} {obj.instructor_last_name}"
    instructor_full_name.short_description = 'Instructor'
    
    def student_id(self, obj):
        return obj.student_license_number
    student_id.short_description = 'ID del alumno'
    
    def instructor_id(self, obj):
        return obj.instructor_license_number
    instructor_id.short_description = 'ID del instructor'
    
    def flight_date_only(self, obj):
        return obj.flight_date.date()
    flight_date_only.short_description = 'Fecha de vuelo'

    class Meta:
        verbose_name = 'Evaluación de vuelo 120-170'
        verbose_name_plural = 'Evaluaciones de vuelo 120-170'

@admin.register(FlightLog)
class FlightLogAdmin(admin.ModelAdmin):
    list_display = [
        'student_full_name', 'student_id',
        'instructor_full_name', 'instructor_id',
        'flight_date_only', 'aircraft_registration', 'session_number', 'session_flight_hours'
    ]
    list_filter = ['flight_date', 'aircraft_registration', 'instructor_id', 'session_grade', 'course_type']
    search_fields = ['student_first_name', 'student_last_name', 'instructor_first_name', 'instructor_last_name']
    date_hierarchy = 'flight_date'
    ordering = ['-flight_date']
    
    fieldsets = (
        ('Sección 1: Datos del alumno', {
            'fields': ('student_id', 'student_first_name', 'student_last_name', 'course_type')
        }),
        ('Sección 2: Datos del instructor', {
            'fields': ('instructor_id', 'instructor_first_name', 'instructor_last_name')
        }),
        ('Sección 3: Datos de la sesión', {
            'fields': (
                'flight_rules', 'solo_flight', 'session_number', 
                'session_letter', 'accumulated_flight_hours', 'session_flight_hours',
                'aircraft_registration', 'session_grade', 'notes'
            )
        }),
    )
    
    readonly_fields = [
        'flight_date', 'student_id', 'student_first_name', 'student_last_name',
        'course_type', 'instructor_id', 'instructor_first_name', 'instructor_last_name',
        'flight_rules', 'solo_flight', 'session_number', 'session_letter',
        'accumulated_flight_hours', 'session_flight_hours', 'aircraft_registration',
        'session_grade', 'notes'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def student_full_name(self, obj):
        return f"{obj.student_first_name} {obj.student_last_name}"
    student_full_name.short_description = 'Alumno'
    
    def instructor_full_name(self, obj):
        return f"{obj.instructor_first_name} {obj.instructor_last_name}"
    instructor_full_name.short_description = 'Instructor'
    
    def student_id(self, obj):
        return obj.student_id
    student_id.short_description = 'ID del alumno'
    
    def instructor_id(self, obj):
        return obj.instructor_id
    instructor_id.short_description = 'ID del instructor'
    
    def flight_date_only(self, obj):
        return obj.flight_date.date()
    flight_date_only.short_description = 'Fecha de vuelo'

    class Meta:
        verbose_name = 'Bitácora de vuelo'
        verbose_name_plural = 'Bitácoras de vuelo'
