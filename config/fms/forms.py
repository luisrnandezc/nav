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
            'course_type', 'flight_rules', 'solo_flight', 'session_number', 'session_letter',
            'accumulated_flight_hours', 'session_flight_hours',
            'aircraft_registration', 'session_grade',
        ]

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
            'student_license_number': forms.NumberInput(attrs={'class': 'form-field'}),
            'course_type': forms.Select(attrs={'class': 'form-field'}),
            'flight_rules': forms.Select(attrs={'class': 'form-field'}),
            'solo_flight': forms.Select(attrs={'class': 'form-field'}),
            'session_number': forms.Select(attrs={'class': 'form-field'}),
            'session_letter': forms.Select(attrs={'class': 'form-field'}),
            'accumulated_flight_hours': forms.NumberInput(attrs={'class': 'form-field'}),
            'session_flight_hours': forms.NumberInput(attrs={'class': 'form-field'}),
            'aircraft_registration': forms.Select(attrs={'class': 'form-field'}),
            'session_grade': forms.Select(attrs={'class': 'form-field'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extract the 'user' argument from kwargs
        super().__init__(*args, **kwargs)
        
        if user:
            profile = user.instructor
            self.fields['instructor_id'].initial = profile.instructor_id
            self.fields['instructor_first_name'].initial = user.first_name
            self.fields['instructor_last_name'].initial = user.last_name
            self.fields['instructor_license_type'].initial = profile.instructor_license_type
            self.fields['instructor_license_number'].initial = profile.instructor_id