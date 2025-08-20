from django.contrib import admin
from django.shortcuts import redirect
from .models import FlightLog, SimulatorLog, SimEvaluation, FlightEvaluation0_100, FlightEvaluation100_120, FlightEvaluation120_170

@admin.register(SimulatorLog)
class SimulatorLogAdmin(admin.ModelAdmin):
    list_display = [
        'evaluation_id',
        'student_full_name', 'student_id',
        'instructor_full_name', 'instructor_id',
        'session_date', 'simulator', 'session_number', 'session_sim_hours'
    ]
    list_filter = ['session_date', 'student_id', 'instructor_id', 'simulator', 'session_grade']
    search_fields = ['student_first_name', 'student_last_name', 'instructor_first_name', 'instructor_last_name']
    date_hierarchy = 'session_date'
    ordering = ['-session_date']
    
    fieldsets = (
        ('Sección 1: Datos del alumno', {
            'fields': ('student_id', 'student_first_name', 'student_last_name', 'course_type')
        }),
        ('Sección 2: Datos del instructor', {
            'fields': ('instructor_id', 'instructor_first_name', 'instructor_last_name')
        }),
        ('Sección 3: Datos de la sesión', {
            'fields': (
                'flight_rules', 'pre_solo_flight', 'session_number', 
                'session_letter', 'accumulated_sim_hours', 'session_sim_hours',
                'simulator', 'session_grade', 'comments'
            )
        }),
    )
    
    readonly_fields = [
        'student_id', 'student_first_name', 'student_last_name', 'course_type',	
        'instructor_id', 'instructor_first_name', 'instructor_last_name',
        'session_grade', 'comments'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_actions(self, request):
        # Remove bulk delete action
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def changelist_view(self, request, extra_context=None):
        # Add custom message explaining why deletion is disabled
        extra_context = extra_context or {}
        extra_context['title'] = 'Bitácoras de simulador (Solo lectura)'
        extra_context['subtitle'] = 'Para eliminar una bitácora, elimine la evaluación correspondiente. Los registros son generados automáticamente.'
        return super().changelist_view(request, extra_context)
    
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

    class Meta:
        verbose_name = 'Bitácora de simulador'
        verbose_name_plural = 'Bitácoras de simulador'

@admin.register(FlightLog)
class FlightLogAdmin(admin.ModelAdmin):
    list_display = [
        'evaluation_id',
        'student_full_name', 'student_id',
        'instructor_full_name', 'instructor_id',
        'session_date', 'aircraft', 'session_number', 'session_flight_hours'
    ]
    list_filter = ['session_date', 'student_id', 'instructor_id', 'aircraft', 'session_grade']
    search_fields = ['student_first_name', 'student_last_name', 'instructor_first_name', 'instructor_last_name']
    date_hierarchy = 'session_date'
    ordering = ['-session_date']
    
    fieldsets = (
        ('Sección 1: Datos del alumno', {
            'fields': ('student_id', 'student_first_name', 'student_last_name', 'course_type')
        }),
        ('Sección 2: Datos del instructor', {
            'fields': ('instructor_id', 'instructor_first_name', 'instructor_last_name')
        }),
        ('Sección 3: Datos de la sesión', {
            'fields': (
                'session_date', 'flight_rules', 'solo_flight', 'session_number', 
                'session_letter', 'accumulated_flight_hours', 'session_flight_hours',
                'aircraft', 'session_grade', 'comments'
            )
        }),
    )
    
    readonly_fields = [
        'student_id', 'student_first_name', 'student_last_name',
        'course_type', 'instructor_id', 'instructor_first_name', 'instructor_last_name',
        'session_grade', 'comments'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_actions(self, request):
        # Remove bulk delete action
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def changelist_view(self, request, extra_context=None):
        # Add custom message explaining why deletion is disabled
        extra_context = extra_context or {}
        extra_context['title'] = 'Bitácoras de vuelo (Solo lectura)'
        extra_context['subtitle'] = 'Para eliminar una bitácora, elimine la evaluación correspondiente. Los registros son generados automáticamente.'
        return super().changelist_view(request, extra_context)
    
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

    class Meta:
        verbose_name = 'Bitácora de vuelo'
        verbose_name_plural = 'Bitácoras de vuelo'

@admin.register(SimEvaluation)
class SimEvaluationAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'student_full_name', 'student_id',
        'instructor_full_name', 'instructor_id',
        'session_date', 'simulator', 'session_number', 'session_sim_hours', 'session_type', 'session_grade'
    ]
    list_filter = ['session_date', 'student_id', 'instructor_id', 'simulator', 'session_grade']
    search_fields = ['student_first_name', 'student_last_name', 'instructor_first_name', 'instructor_last_name']
    date_hierarchy = 'session_date'
    ordering = ['-session_date']

    actions = ['generate_pdf']
    
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
                'session_date', 'flight_rules', 'pre_solo_flight', 'session_number', 
                'session_letter', 'accumulated_sim_hours', 'session_sim_hours',
                'simulator', 'session_grade', 'session_type'
            )
        }),
        ('Sección 4: Prevuelo', {
            'fields': ('pre_1', 'pre_2', 'pre_3'),
            'classes': ('collapse',)
        }),
        ('Sección 5: Despegue', {
            'fields': ('to_1', 'to_2', 'to_3', 'to_4', 'to_5'),
            'classes': ('collapse',)
        }),
        ('Sección 6: Procedimiento de salida', {
            'fields': ('dep_1', 'dep_2', 'dep_3', 'dep_4', 'dep_5'),
            'classes': ('collapse',)
        }),
        ('Sección 7: Instrumentos básicos', {
            'fields': ('inst_1', 'inst_2', 'inst_3', 'inst_4', 'inst_5', 'inst_6',
                'inst_7', 'inst_8', 'inst_9', 'inst_10', 'inst_11', 'inst_12', 'inst_13'
            ),
            'classes': ('collapse',)
        }),
        ('Sección 9: Misceláneos', {
            'fields': ('misc_1', 'misc_2', 'misc_3', 'misc_4', 'misc_5', 'misc_6', 'misc_7'),
            'classes': ('collapse',)
        }),
        ('Sección 10: Uso de radioayudas (VOR)', {
            'fields': ('radio_1', 'radio_2', 'radio_3', 'radio_4', 'radio_5', 'radio_6', 
                       'radio_7', 'radio_8', 'radio_9', 'radio_10', 'radio_11'
            ),
            'classes': ('collapse',)
        }),
        ('Sección 11: Uso de radioayudas (ADF)', {
            'fields': ('radio_12', 'radio_13', 'radio_14', 'radio_15', 'radio_16', 'radio_17', 
                       'radio_18', 'radio_19', 'radio_20', 'radio_21', 'radio_22'
            ),
            'classes': ('collapse',)
        }),
        ('Sección 12: Aproximaciones (ILS)', {
            'fields': ('app_1', 'app_2', 'app_3', 'app_4', 
                       'app_5', 'app_6', 'app_7', 'app_8'
            ),
            'classes': ('collapse',)
        }),
        ('Sección 13: Aproximaciones (VOR)', {
            'fields': ('app_9', 'app_10', 'app_11', 'app_12', 
                       'app_13', 'app_14', 'app_15', 'app_16'
            ),
            'classes': ('collapse',)
        }),
        ('Sección 14: Aproximaciones (ADF)', {
            'fields': ('app_17', 'app_18', 'app_19', 'app_20', 
                       'app_21', 'app_22', 'app_23', 'app_24'
            ),
            'classes': ('collapse',)
        }),
        ('Sección 15: Go-Around', {
            'fields': ('go_1', 'go_2'),
            'classes': ('collapse',)
        }),
        ('Sección 16: Comentarios', {
            'fields': ('comments',)
        }),
    )
    
    readonly_fields = [
            'instructor_id', 'instructor_first_name', 'instructor_last_name',
            'instructor_license_type', 'instructor_license_number',
            'student_id', 'student_first_name', 'student_last_name',
            'student_license_type', 'student_license_number', 
            'course_type', 
            'session_date', 'flight_rules', 'pre_solo_flight', 'session_number', 'session_letter', 
            'accumulated_sim_hours', 'session_sim_hours', 'simulator', 'session_grade', 'session_type',
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
            'comments'
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

    def generate_pdf(self, request, queryset):
        """Generate PDF for selected evaluations."""
        if len(queryset) == 1:
            # Single evaluation - redirect to PDF download
            evaluation = queryset.first()
            return redirect('fms:download_pdf', form_type='sim', evaluation_id=evaluation.id)
        else:
            # Multiple evaluations - show message
            self.message_user(request, f'Seleccione solo una evaluación para generar el PDF.')
            return
    generate_pdf.short_description = "Generar PDF de la evaluación seleccionada"
    
    def delete_model(self, request, obj):
        obj.delete()
    
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()

    class Meta:
        verbose_name = 'Evaluación de simulador'
        verbose_name_plural = 'Evaluaciones de simulador'

@admin.register(FlightEvaluation0_100)
class FlightEvaluation0_100Admin(admin.ModelAdmin):
    list_display = [
        'id',
        'student_full_name', 'student_id',
        'instructor_full_name', 'instructor_id',
        'session_date', 'aircraft', 'session_number', 'session_flight_hours', 'session_grade'
    ]
    list_filter = ['session_date', 'student_id', 'instructor_id', 'aircraft', 'session_grade']
    search_fields = ['student_first_name', 'student_last_name', 'instructor_first_name', 'instructor_last_name']
    date_hierarchy = 'session_date'
    ordering = ['-session_date']
    
    actions = ['generate_pdf']
    
    def generate_pdf(self, request, queryset):
        """Generate PDF for selected evaluations."""
        if len(queryset) == 1:
            # Single evaluation - redirect to PDF download
            evaluation = queryset.first()
            return redirect('fms:download_pdf', form_type='0_100', evaluation_id=evaluation.id)
        else:
            # Multiple evaluations - show message
            self.message_user(request, f'Seleccione solo una evaluación para generar el PDF.')
            return
    generate_pdf.short_description = "Generar PDF de la evaluación seleccionada"
    
    def delete_model(self, request, obj):
        obj.delete()
    
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()
    
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
                'session_date', 'flight_rules', 'solo_flight', 'session_number', 
                'session_letter', 'accumulated_flight_hours', 'session_flight_hours',
                'initial_hourmeter', 'final_hourmeter', 'fuel_consumed',
                'aircraft', 'session_grade'
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
        ('Sección 11: Comentarios', {
            'fields': ('comments',)
        }),
    )
    
    readonly_fields = [
        'student_id', 'student_first_name', 'student_last_name', 
        'student_license_type', 'student_license_number', 'course_type',
        'instructor_id', 'instructor_first_name', 'instructor_last_name',
        'instructor_license_type', 'instructor_license_number',
        'session_date', 'flight_rules', 'solo_flight', 'session_number', 
        'session_letter', 'accumulated_flight_hours', 'session_flight_hours', 
        'initial_hourmeter', 'final_hourmeter', 'fuel_consumed',
        'aircraft', 'session_grade',
        'pre_1', 'pre_2', 'pre_3',
        'pre_4', 'pre_5', 'pre_6', 'to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6', 'mvrs_1', 'mvrs_2',
        'mvrs_3', 'mvrs_4', 'mvrs_5', 'mvrs_6', 'mvrs_7', 'mvrs_8', 'mvrs_9', 'mvrs_10', 'mvrs_11',
        'mvrs_12', 'mvrs_13', 'mvrs_14', 'mvrs_15', 'mvrs_16', 'mvrs_17', 'mvrs_18', 'emer_1', 'emer_2',
        'emer_3', 'emer_4', 'emer_5', 'emer_6', 'nav_1', 'nav_2', 'nav_3', 'nav_4', 'nav_5', 'nav_6',
        'gen_1', 'gen_2', 'gen_3', 'gen_4', 'gen_5', 'gen_6', 'gen_7', 'land_1', 'land_2', 'land_3',
        'land_4', 'land_5', 'land_6', 'land_7', 'land_8', 'land_9', 'land_10', 'comments'
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

    def delete_model(self, request, obj):
        obj.delete()
    
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()
    
    class Meta:
        verbose_name = 'Evaluación de vuelo 0-100'
        verbose_name_plural = 'Evaluaciones de vuelo 0-100'

@admin.register(FlightEvaluation100_120)
class FlightEvaluation100_120Admin(admin.ModelAdmin):
    list_display = [
        'id',
        'student_full_name', 'student_id',
        'instructor_full_name', 'instructor_id',
        'session_date', 'aircraft', 'session_number', 'session_flight_hours', 'session_grade'
    ]
    list_filter = ['session_date', 'student_id', 'instructor_id', 'aircraft', 'session_grade']
    search_fields = ['student_first_name', 'student_last_name', 'instructor_first_name', 'instructor_last_name']
    date_hierarchy = 'session_date'
    ordering = ['-session_date']

    actions = ['generate_pdf']
    
    def generate_pdf(self, request, queryset):
        """Generate PDF for selected evaluations."""
        if len(queryset) == 1:
            # Single evaluation - redirect to PDF download
            evaluation = queryset.first()
            return redirect('fms:download_pdf', form_type='100_120', evaluation_id=evaluation.id)
        else:
            # Multiple evaluations - show message
            self.message_user(request, f'Seleccione solo una evaluación para generar el PDF.')
            return
    generate_pdf.short_description = "Generar PDF de la evaluación seleccionada"
    
    def delete_model(self, request, obj):
        obj.delete()
    
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()
    
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
                'session_date', 'flight_rules', 'solo_flight', 'session_number', 
                'session_letter', 'accumulated_flight_hours', 'session_flight_hours',
                'aircraft', 'session_grade'
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
        ('Sección 11: Comentarios', {
            'fields': ('comments',)
        }),
    )
    
    readonly_fields = [
        'student_id', 'student_first_name', 'student_last_name', 
        'student_license_type', 'student_license_number', 'course_type',
        'instructor_id', 'instructor_first_name', 'instructor_last_name',
        'instructor_license_type', 'instructor_license_number',
        'session_date', 'flight_rules', 'solo_flight', 'session_number', 
        'session_letter', 'accumulated_flight_hours', 'session_flight_hours', 
        'aircraft', 'session_grade',
        'pre_1', 'pre_2', 'pre_3', 'pre_4',
        'pre_5', 'pre_6', 'to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6', 'b_ifr_1',
        'b_ifr_2', 'b_ifr_3', 'b_ifr_4', 'b_ifr_5', 'b_ifr_6', 'b_ifr_7', 'b_ifr_8',
        'b_ifr_9', 'b_ifr_10', 'b_ifr_11', 'a_ifr_1', 'a_ifr_2', 'a_ifr_3', 'a_ifr_4',
        'a_ifr_5', 'a_ifr_6', 'a_ifr_7', 'a_ifr_8', 'a_ifr_9', 'a_ifr_10', 'a_ifr_11',
        'land_1', 'land_2', 'land_3', 'land_4', 'land_5', 'land_6', 'land_7', 'emer_1',
        'emer_2', 'emer_3', 'emer_4', 'emer_5', 'gen_1', 'gen_2', 'gen_3', 'gen_4',
        'gen_5', 'gen_6', 'gen_7', 'comments'
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
    
    class Meta:
        verbose_name = 'Evaluación de vuelo 100-120'
        verbose_name_plural = 'Evaluaciones de vuelo 100-120'

@admin.register(FlightEvaluation120_170)
class FlightEvaluation120_170Admin(admin.ModelAdmin):
    list_display = [
        'id',
        'student_full_name', 'student_id',
        'instructor_full_name', 'instructor_id',
        'session_date', 'aircraft', 'session_number', 'session_flight_hours', 'session_grade'
    ]
    list_filter = ['session_date', 'student_id', 'instructor_id', 'aircraft', 'session_grade']
    search_fields = ['student_first_name', 'student_last_name', 'instructor_first_name', 'instructor_last_name']
    date_hierarchy = 'session_date'
    ordering = ['-session_date']

    actions = ['generate_pdf']
    
    def generate_pdf(self, request, queryset):
        """Generate PDF for selected evaluations."""
        if len(queryset) == 1:
            # Single evaluation - redirect to PDF download
            evaluation = queryset.first()
            return redirect('fms:download_pdf', form_type='120_170', evaluation_id=evaluation.id)
        else:
            # Multiple evaluations - show message
            self.message_user(request, f'Seleccione solo una evaluación para generar el PDF.')
            return
    generate_pdf.short_description = "Generar PDF de la evaluación seleccionada"
    
    def delete_model(self, request, obj):
        obj.delete()
    
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()
    
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
                'session_date', 'flight_rules', 'solo_flight', 'session_number', 
                'session_letter', 'accumulated_flight_hours', 'session_flight_hours',
                'aircraft', 'session_grade'
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
        ('Sección 10: Comentarios', {
            'fields': ('comments',)
        }),
    )
    
    readonly_fields = [
        'student_id', 'student_first_name', 'student_last_name', 
        'student_license_type', 'student_license_number', 'course_type',
        'instructor_id', 'instructor_first_name', 'instructor_last_name',
        'instructor_license_type', 'instructor_license_number',
        'session_date', 'flight_rules', 'solo_flight', 'session_number', 
        'session_letter', 'accumulated_flight_hours', 'session_flight_hours', 
        'aircraft', 'session_grade',
        'pre_1', 'pre_2', 'pre_3', 'pre_4',
        'pre_5', 'pre_6', 'to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6', 'inst_1',
        'inst_2', 'inst_3', 'inst_4', 'inst_5', 'inst_6', 'inst_7', 'inst_8', 'inst_9',
        'inst_10', 'inst_11', 'land_1', 'land_2', 'land_3', 'land_4', 'land_5', 'land_6',
        'land_7', 'emer_1', 'emer_2', 'emer_3', 'emer_4', 'gen_1', 'gen_2', 'gen_3',
        'gen_4', 'gen_5', 'gen_6', 'gen_7', 'comments'
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
    
    class Meta:
        verbose_name = 'Evaluación de vuelo 120-170'
        verbose_name_plural = 'Evaluaciones de vuelo 120-170'