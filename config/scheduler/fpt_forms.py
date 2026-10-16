"""Validated inputs for staff FPT calendar actions."""

from django import forms

from .models import FPTPeriod, FPTSession


class FPTPeriodForm(forms.ModelForm):
    class Meta:
        model = FPTPeriod
        fields = ['start_date', 'end_date', 'is_active']


class FPTSessionForm(forms.ModelForm):
    class Meta:
        model = FPTSession
        fields = [
            'period', 'date', 'start_hour', 'status', 'student',
            'external_student_name', 'instructor', 'external_instructor_name',
            'category', 'notes',
        ]
