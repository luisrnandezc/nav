from django.contrib import admin
from .models import FlightEvaluation0_100, FlightEvaluation100_120, FlightLog

@admin.register(FlightEvaluation0_100)
class FlightEvaluation0_100Admin(admin.ModelAdmin):
    list_display = ['student_first_name', 'student_last_name', 'instructor_first_name', 'instructor_last_name', 'flight_date', 'session_number', 'session_letter']
    list_filter = ['flight_date', 'aircraft_registration', 'instructor_license_number', 'session_grade', 'course_type']
    search_fields = ['student_first_name', 'student_last_name', 'instructor_first_name', 'instructor_last_name']
    date_hierarchy = 'flight_date'
    ordering = ['-flight_date']
    
    class Meta:
        verbose_name = 'Flight Evaluation 0-100'
        verbose_name_plural = 'Flight Evaluations 0-100'

@admin.register(FlightEvaluation100_120)
class FlightEvaluation100_120Admin(admin.ModelAdmin):
    list_display = ['student_first_name', 'student_last_name', 'instructor_first_name', 'instructor_last_name', 'flight_date', 'session_number', 'session_letter']
    list_filter = ['flight_date', 'aircraft_registration', 'instructor_license_number', 'session_grade', 'course_type']
    search_fields = ['student_first_name', 'student_last_name', 'instructor_first_name', 'instructor_last_name']
    date_hierarchy = 'flight_date'
    ordering = ['-flight_date']
    
    class Meta:
        verbose_name = 'Flight Evaluation 100-120'
        verbose_name_plural = 'Flight Evaluations 100-120'

@admin.register(FlightLog)
class FlightLogAdmin(admin.ModelAdmin):
    list_display = ['student_first_name', 'student_last_name', 'instructor_first_name', 'instructor_last_name', 'flight_date', 'session_number', 'session_letter', 'session_flight_hours']
    list_filter = ['flight_date', 'aircraft_registration', 'instructor_id', 'session_grade', 'course_type']
    search_fields = ['student_first_name', 'student_last_name', 'instructor_first_name', 'instructor_last_name']
    date_hierarchy = 'flight_date'
    ordering = ['-flight_date']
    
    class Meta:
        verbose_name = 'Flight Log'
        verbose_name_plural = 'Flight Logs'
