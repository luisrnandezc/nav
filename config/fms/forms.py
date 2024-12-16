from django import forms
from .models import FlightEvaluation

class FlightEvaluationForm(forms.ModelForm):
    class Meta:
        model = FlightEvaluation
        fields = [
            'instructor_id', 'instructor_first_name', 'instructor_last_name',
            'instructor_license_type', 'instructor_license_number',
            'student_id', 'student_first_name', 'student_last_name',
            'student_license_type', 'student_license_number',
            'course_type', 'flight_rules', 'solo_flight', 'session_number',
            'accumulated_flight_hours', 'session_flight_hours',
            'aircraft_registration', 'session_grade',
        ]