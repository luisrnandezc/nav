from django.contrib import admin
from django import forms
from django.db import transaction
from django.shortcuts import redirect
from accounts.models import StudentProfile
from fleet.models import Aircraft
from .models import SimEvaluation, FlightEvaluation0_100, FlightEvaluation100_120, FlightEvaluation120_170, ExternalFlightEvaluation, FlightReport, DiscrepancyReport


def flight_evaluation_aircraft(obj):
    return obj.aircraft


flight_evaluation_aircraft.short_description = 'Aeronave'
flight_evaluation_aircraft.admin_order_field = 'aircraft'


def flight_evaluation_hours(obj):
    return obj.session_flight_hours


flight_evaluation_hours.short_description = 'Horas'
flight_evaluation_hours.admin_order_field = 'session_flight_hours'


def corrected_flight_hours(aircraft, initial_hourmeter, final_hourmeter):
    if initial_hourmeter is None or final_hourmeter is None:
        raise forms.ValidationError('El horómetro inicial y final son requeridos.')
    if final_hourmeter < initial_hourmeter:
        raise forms.ValidationError('El horómetro final no puede ser menor que el inicial.')

    hours = round(final_hourmeter - initial_hourmeter, 1)
    if aircraft.registration == 'YV206E':
        hours = round(hours * aircraft.hour_correction_factor, 1)
    if hours > 14:
        raise forms.ValidationError('Las horas corregidas no pueden exceder 14 horas.')
    return hours


class FlightEvaluationCorrectionForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        fuel_consumed = cleaned_data.get('fuel_consumed')
        if fuel_consumed is not None and fuel_consumed < 0:
            self.add_error('fuel_consumed', 'El combustible consumido no puede ser negativo.')

        try:
            corrected_flight_hours(
                self.instance.aircraft,
                cleaned_data.get('initial_hourmeter'),
                cleaned_data.get('final_hourmeter'),
            )
        except forms.ValidationError as error:
            raise forms.ValidationError(error.messages)
        return cleaned_data


class FlightEvaluationCorrectionAdminMixin:
    form = FlightEvaluationCorrectionForm

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if not change:
            return super().save_model(request, obj, form, change)

        original = self.model.objects.select_for_update().get(pk=obj.pk)
        student = StudentProfile.objects.select_for_update().get(
            user__national_id=original.student_id
        )
        aircraft = Aircraft.objects.select_for_update().get(pk=original.aircraft_id)
        new_hours = corrected_flight_hours(
            aircraft, obj.initial_hourmeter, obj.final_hourmeter
        )
        hours_difference = new_hours - original.session_flight_hours

        old_charge = round(
            original.session_flight_hours * original.hourly_rate_applied
            + original.fuel_consumed * original.fuel_rate_applied,
            2,
        )
        new_charge = round(
            new_hours * original.hourly_rate_applied
            + obj.fuel_consumed * original.fuel_rate_applied,
            2,
        )

        new_student_hours = student.flight_hours + hours_difference
        new_nav_hours = student.nav_flight_hours + hours_difference
        new_aircraft_hours = aircraft.total_hours + hours_difference
        if new_student_hours < 0 or new_nav_hours < 0 or new_aircraft_hours < 0:
            raise forms.ValidationError(
                'La corrección produciría un total de horas negativo.'
            )

        obj.session_flight_hours = new_hours
        super().save_model(request, obj, form, change)

        student.flight_hours = new_student_hours
        student.nav_flight_hours = new_nav_hours
        student.balance += old_charge - new_charge
        student.save(update_fields=['flight_hours', 'nav_flight_hours', 'balance'])

        aircraft.total_hours = new_aircraft_hours
        aircraft.save(update_fields=['total_hours'])

@admin.register(SimEvaluation)
class SimEvaluationAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'student_full_name', 'student_id',
        'instructor_full_name', 'instructor_id',
        'session_date', 'simulator', 'session_number', 'session_sim_hours', 'session_type', 'session_grade', 
        'aura_processed',
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
        ('Sección 8: Actitudes anormales', {
            'fields': ('upset_1', 'upset_2', 'upset_3'),
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
            'fields': ('comments', 'aura_processed', 'aura_review'),
        }),
    )
    
    readonly_fields = [
            'student_id', 'student_first_name', 'student_last_name',
            'student_license_type', 'student_license_number', 
            'session_sim_hours', 'simulator', 'session_type',
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
            'comments', 'aura_processed', 'aura_review'
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
class FlightEvaluation0_100Admin(FlightEvaluationCorrectionAdminMixin, admin.ModelAdmin):
    list_display = [
        'id',
        'student_full_name', 'student_id',
        'instructor_full_name', 'instructor_id',
        'session_date', flight_evaluation_aircraft, 'session_number', flight_evaluation_hours, 'session_grade',
        'aura_processed',
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
        ('Sección 5: Despegue / Salida visual', {
            'fields': ('to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6'),
            'classes': ('collapse',)
        }),
        ('Sección 6: Maniobras básicas / avanzadas', {
            'fields': (
                'mvrs_1', 'mvrs_2', 'mvrs_3', 'mvrs_4', 'mvrs_5', 'mvrs_6',
                'mvrs_7', 'mvrs_8', 'mvrs_9', 'mvrs_10', 'mvrs_11', 'mvrs_12',
                'mvrs_13', 'mvrs_14', 'mvrs_15', 'mvrs_16', 'mvrs_17', 'mvrs_18'
            ),
            'classes': ('collapse',)
        }),
        ('Sección 7: Navegación VFR', {
            'fields': ('nav_1', 'nav_2', 'nav_3', 'nav_4', 'nav_5', 'nav_6'),
            'classes': ('collapse',)
        }),
        ('Sección 8: Circuito / Procedimiento', {
            'fields': (
                'land_1', 'land_2', 'land_3', 'land_4', 'land_5',
                'land_6', 'land_7', 'land_8', 'land_9', 'land_10'
            ),
            'classes': ('collapse',)
        }),
        ('Sección 9: Emergencias', {
            'fields': ('emer_1', 'emer_2', 'emer_3', 'emer_4', 'emer_5', 'emer_6'),
            'classes': ('collapse',)
        }),
        ('Sección 10: Evaluación general', {
            'fields': ('gen_1', 'gen_2', 'gen_3', 'gen_4', 'gen_5', 'gen_6', 'gen_7'),
            'classes': ('collapse',)
        }),
        ('Sección 11: Comentarios', {
            'fields': ('comments', 'aura_processed', 'aura_review')
        }),
    )
    
    readonly_fields = [
        'student_id', 'student_first_name', 'student_last_name', 
        'student_license_type', 'student_license_number',
        'session_flight_hours',
        'aircraft',
        'pre_1', 'pre_2', 'pre_3',
        'pre_4', 'pre_5', 'pre_6', 'to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6', 'mvrs_1', 'mvrs_2',
        'mvrs_3', 'mvrs_4', 'mvrs_5', 'mvrs_6', 'mvrs_7', 'mvrs_8', 'mvrs_9', 'mvrs_10', 'mvrs_11',
        'mvrs_12', 'mvrs_13', 'mvrs_14', 'mvrs_15', 'mvrs_16', 'mvrs_17', 'mvrs_18', 'emer_1', 'emer_2',
        'emer_3', 'emer_4', 'emer_5', 'emer_6', 'nav_1', 'nav_2', 'nav_3', 'nav_4', 'nav_5', 'nav_6',
        'gen_1', 'gen_2', 'gen_3', 'gen_4', 'gen_5', 'gen_6', 'gen_7', 'land_1', 'land_2', 'land_3',
        'land_4', 'land_5', 'land_6', 'land_7', 'land_8', 'land_9', 'land_10', 
        'comments', 'aura_processed', 'aura_review'
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
class FlightEvaluation100_120Admin(FlightEvaluationCorrectionAdminMixin, admin.ModelAdmin):
    list_display = [
        'id',
        'student_full_name', 'student_id',
        'instructor_full_name', 'instructor_id',
        'session_date', flight_evaluation_aircraft, 'session_number', flight_evaluation_hours, 'session_grade',
        'aura_processed',
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
                'initial_hourmeter', 'final_hourmeter', 'fuel_consumed',
                'aircraft', 'session_grade'
            )
        }),
        ('Sección 4: Prevuelo / Encendido / Taxeo', {
            'fields': ('pre_1', 'pre_2', 'pre_3', 'pre_4', 'pre_5', 'pre_6'),
            'classes': ('collapse',)
        }),
        ('Sección 5: Despegue / Salida instrumental', {
            'fields': ('to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6'),
            'classes': ('collapse',)
        }),
        ('Sección 6: Maniobras IFR básicas', {
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
        ('Sección 10: Evaluación general', {
            'fields': ('gen_1', 'gen_2', 'gen_3', 'gen_4', 'gen_5', 'gen_6', 'gen_7'),
            'classes': ('collapse',)
        }),
        ('Sección 11: Comentarios', {
            'fields': ('comments', 'aura_processed', 'aura_review')
        }),
    )
    
    readonly_fields = [
        'student_id', 'student_first_name', 'student_last_name', 
        'student_license_type', 'student_license_number',
        'session_flight_hours',
        'aircraft',
        'pre_1', 'pre_2', 'pre_3', 'pre_4',
        'pre_5', 'pre_6', 'to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6', 'b_ifr_1',
        'b_ifr_2', 'b_ifr_3', 'b_ifr_4', 'b_ifr_5', 'b_ifr_6', 'b_ifr_7', 'b_ifr_8',
        'b_ifr_9', 'b_ifr_10', 'b_ifr_11', 'a_ifr_1', 'a_ifr_2', 'a_ifr_3', 'a_ifr_4',
        'a_ifr_5', 'a_ifr_6', 'a_ifr_7', 'a_ifr_8', 'a_ifr_9', 'a_ifr_10', 'a_ifr_11',
        'land_1', 'land_2', 'land_3', 'land_4', 'land_5', 'land_6', 'land_7', 'emer_1',
        'emer_2', 'emer_3', 'emer_4', 'emer_5', 'gen_1', 'gen_2', 'gen_3', 'gen_4',
        'gen_5', 'gen_6', 'gen_7', 
        'comments', 'aura_processed', 'aura_review'
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
class FlightEvaluation120_170Admin(FlightEvaluationCorrectionAdminMixin, admin.ModelAdmin):
    list_display = [
        'id',
        'student_full_name', 'student_id',
        'instructor_full_name', 'instructor_id',
        'session_date', flight_evaluation_aircraft, 'session_number', flight_evaluation_hours, 'session_grade',
        'aura_processed',
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
                'initial_hourmeter', 'final_hourmeter', 'fuel_consumed',
                'aircraft', 'session_grade'
            )
        }),
        ('Sección 4: Prevuelo / Encendido / Taxeo', {
            'fields': ('pre_1', 'pre_2', 'pre_3', 'pre_4', 'pre_5', 'pre_6'),
            'classes': ('collapse',)
        }),
        ('Sección 5: Despegue / Salida VFR/IFR', {
            'fields': ('to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6'),
            'classes': ('collapse',)
        }),
        ('Sección 6: Instrumentos avanzados', {
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
        ('Sección 8: Emergencias situacionales (simuladas)', {
            'fields': ('emer_1', 'emer_2', 'emer_3', 'emer_4'),
            'classes': ('collapse',)
        }),
        ('Sección 9: Evaluación general', {
            'fields': ('gen_1', 'gen_2', 'gen_3', 'gen_4', 'gen_5', 'gen_6', 'gen_7'),
            'classes': ('collapse',)
        }),
        ('Sección 10: Comentarios', {
            'fields': ('comments', 'aura_processed', 'aura_review')
        }),
    )
    
    readonly_fields = [
        'student_id', 'student_first_name', 'student_last_name', 
        'student_license_type', 'student_license_number',
        'session_flight_hours', 
        'aircraft',
        'pre_1', 'pre_2', 'pre_3', 'pre_4',
        'pre_5', 'pre_6', 'to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6', 'inst_1',
        'inst_2', 'inst_3', 'inst_4', 'inst_5', 'inst_6', 'inst_7', 'inst_8', 'inst_9',
        'inst_10', 'inst_11', 'land_1', 'land_2', 'land_3', 'land_4', 'land_5', 'land_6',
        'land_7', 'emer_1', 'emer_2', 'emer_3', 'emer_4', 'gen_1', 'gen_2', 'gen_3',
        'gen_4', 'gen_5', 'gen_6', 'gen_7',
        'comments', 'aura_processed', 'aura_review'
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


@admin.register(ExternalFlightEvaluation)
class ExternalFlightEvaluationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'student_full_name', 'student_id',
        'instructor_full_name', 'instructor_id', 'session_date',
        'aircraft_display', 'evaluation_type', 'session_number',
        'session_hours', 'session_grade',
    )
    list_filter = ('session_date', 'student_id', 'instructor_id', 'evaluation_type', 'session_grade')
    search_fields = (
        'student_first_name', 'student_last_name', 'student_id',
        'instructor_first_name', 'instructor_last_name', 'aircraft_registration',
    )
    readonly_fields = (
        'student_id', 'student_first_name', 'student_last_name',
        'student_license_type', 'student_license_number', 'session_flight_hours',
        'initial_hourmeter', 'final_hourmeter', 'aircraft_registration',
        'grades', 'comments',
    )
    ordering = ('-session_date', '-id')
    actions = ('generate_pdf',)

    fieldsets = (
        ('Sección 1: Datos del alumno', {
            'fields': (
                'student_id', 'student_first_name', 'student_last_name',
                'student_license_type', 'student_license_number', 'course_type',
            ),
        }),
        ('Sección 2: Datos del instructor', {
            'fields': (
                'instructor_id', 'instructor_first_name', 'instructor_last_name',
                'instructor_license_type', 'instructor_license_number',
            ),
        }),
        ('Sección 3: Datos de la evaluación y sesión', {
            'fields': (
                'evaluation_type', 'session_date', 'flight_rules', 'solo_flight',
                'session_number', 'session_letter', 'accumulated_flight_hours',
                'session_flight_hours', 'initial_hourmeter', 'final_hourmeter',
                'fuel_consumed', 'aircraft_registration', 'session_grade',
            ),
        }),
        ('Sección 4: Prevuelo / Encendido / Taxeo', {
            'fields': tuple(f'grade_pre_{i}' for i in range(1, 7)),
            'classes': ('collapse',),
        }),
        ('Sección 5: Despegue / Salida VFR/IFR', {
            'fields': tuple(f'grade_to_{i}' for i in range(1, 7)),
            'classes': ('collapse',),
        }),
        ('Sección 6: Instrumentos avanzados', {
            'fields': tuple(f'grade_inst_{i}' for i in range(1, 12)),
            'classes': ('collapse',),
        }),
        ('Sección 7: Maniobras', {
            'fields': tuple(f'grade_mvrs_{i}' for i in range(1, 14)),
            'classes': ('collapse',),
        }),
        ('Sección 8: Navegación VFR', {
            'fields': tuple(f'grade_nav_{i}' for i in range(1, 7)),
            'classes': ('collapse',),
        }),
        ('Sección 9: Aproximación final y aterrizaje', {
            'fields': tuple(f'grade_land_{i}' for i in range(1, 8)),
            'classes': ('collapse',),
        }),
        ('Sección 10: Emergencias situacionales (simuladas)', {
            'fields': tuple(f'grade_emer_{i}' for i in range(1, 5)),
            'classes': ('collapse',),
        }),
        ('Sección 11: Evaluación general', {
            'fields': tuple(f'grade_gen_{i}' for i in range(1, 8)),
            'classes': ('collapse',),
        }),
        ('Sección 12: Comentarios', {'fields': ('comments',)}),
    )

    def get_readonly_fields(self, request, obj=None):
        grade_fields = tuple(
            f'grade_{name}' for name in (
                *(f'pre_{i}' for i in range(1, 7)),
                *(f'to_{i}' for i in range(1, 7)),
                *(f'inst_{i}' for i in range(1, 12)),
                *(f'mvrs_{i}' for i in range(1, 14)),
                *(f'nav_{i}' for i in range(1, 7)),
                *(f'land_{i}' for i in range(1, 8)),
                *(f'emer_{i}' for i in range(1, 5)),
                *(f'gen_{i}' for i in range(1, 8)),
            )
        )
        return self.readonly_fields + grade_fields

    def student_full_name(self, obj):
        return f'{obj.student_first_name} {obj.student_last_name}'

    student_full_name.short_description = 'Alumno'

    def instructor_full_name(self, obj):
        return f'{obj.instructor_first_name} {obj.instructor_last_name}'

    instructor_full_name.short_description = 'Instructor'

    def aircraft_display(self, obj):
        return obj.aircraft_registration

    aircraft_display.short_description = 'Aeronave'
    aircraft_display.admin_order_field = 'aircraft_registration'

    def session_hours(self, obj):
        return obj.session_flight_hours

    session_hours.short_description = 'Horas'

    def generate_pdf(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Seleccione solo una evaluación para generar el PDF.')
            return None
        evaluation = queryset.first()
        return redirect('fms:download_pdf', form_type='external', evaluation_id=evaluation.id)

    generate_pdf.short_description = 'Generar PDF de la evaluación seleccionada'


def _external_grade_admin_method(field_name):
    def display_grade(self, obj):
        return obj.grades.get(field_name, 'NE')

    display_grade.short_description = FlightEvaluation120_170._meta.get_field(field_name).verbose_name
    return display_grade


for _grade_name in (
    *(f'pre_{i}' for i in range(1, 7)),
    *(f'to_{i}' for i in range(1, 7)),
    *(f'inst_{i}' for i in range(1, 12)),
    *(f'mvrs_{i}' for i in range(1, 14)),
    *(f'nav_{i}' for i in range(1, 7)),
    *(f'land_{i}' for i in range(1, 8)),
    *(f'emer_{i}' for i in range(1, 5)),
    *(f'gen_{i}' for i in range(1, 8)),
):
    setattr(ExternalFlightEvaluationAdmin, f'grade_{_grade_name}', _external_grade_admin_method(_grade_name))

@admin.register(FlightReport)
class FlightReportAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'pilot_full_name', 'pilot_id', 'flight_date', 'aircraft', 
        'flight_reason', 'flight_hours', 'fuel_consumed'
    ]
    list_filter = ['flight_date', 'pilot_id', 'aircraft', 'flight_reason']
    search_fields = ['pilot_id', 'pilot_first_name', 'pilot_last_name']
    date_hierarchy = 'flight_date'
    ordering = ['-flight_date']

    def delete_model(self, request, obj):
        obj.delete()
    
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()
    
    fieldsets = (
        ('Sección 1: Datos del piloto', {
            'fields': (
                'pilot_id', 'pilot_first_name', 'pilot_last_name', 
                'pilot_license_number'
            )
        }),
        ('Sección 2: Datos del vuelo', {
            'fields': (
                'flight_date', 'flight_reason', 'aircraft', 'initial_hourmeter',
                'final_hourmeter', 'fuel_consumed'
            )
        }),
        ('Sección 3: Comentarios', {
            'fields': ('comments', 'aura_processed')
        }),
    )
    readonly_fields = [
        'pilot_id', 'pilot_first_name', 'pilot_last_name', 
        'pilot_license_number', 'flight_date', 'flight_reason', 'aircraft', 
        'initial_hourmeter', 'final_hourmeter', 'fuel_consumed', 'comments'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def pilot_full_name(self, obj):
        return f"{obj.pilot_first_name} {obj.pilot_last_name}"
    pilot_full_name.short_description = 'Piloto'
    
    class Meta:
        verbose_name = 'Reporte de vuelo'
        verbose_name_plural = 'Reportes de vuelo'

@admin.register(DiscrepancyReport)
class DiscrepancyReportAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'aircraft',
        'reportee_full_name',
        'discrepancy_type',
        'status',
        'created_at',
        'updated_at'
    ]
    list_filter = ['status', 'discrepancy_type', 'aircraft', 'created_at']
    search_fields = [
        'aircraft__registration',
        'reportee_first_name',
        'reportee_last_name',
        'discrepancy_description'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información de la aeronave', {
            'fields': ('aircraft',)
        }),
        ('Información del reportante', {
            'fields': ('reportee_first_name', 'reportee_last_name')
        }),
        ('Detalles de la discrepancia', {
            'fields': ('discrepancy_type', 'discrepancy_description')
        }),
        ('Estado y fechas', {
            'fields': ('status', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def reportee_full_name(self, obj):
        return f"{obj.reportee_first_name} {obj.reportee_last_name}"
    reportee_full_name.short_description = 'Reportante'
    
    class Meta:
        verbose_name = 'Reporte de discrepancia'
        verbose_name_plural = 'Reportes de discrepancia'
