from django import forms

from accounts.models import InstructorProfile, StudentProfile
from fleet.models import Aircraft, Simulator


class ProductionFilterForm(forms.Form):
    """GET filters accepted by the production panel and reporting service."""

    start_date = forms.DateField(
        label='Fecha inicial',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'ui-input'}),
    )
    end_date = forms.DateField(
        label='Fecha final',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'ui-input'}),
    )
    aircraft = forms.ModelChoiceField(
        label='Aeronaves',
        queryset=Aircraft.objects.order_by('registration'),
        required=False,
        empty_label='All - Todos',
        widget=forms.Select(attrs={'class': 'ui-select'}),
    )
    simulators = forms.ModelChoiceField(
        label='Simuladores',
        queryset=Simulator.objects.order_by('name'),
        required=False,
        empty_label='All - Todos',
        widget=forms.Select(attrs={'class': 'ui-select'}),
    )
    instructors = forms.ModelChoiceField(
        label='Instructores',
        queryset=InstructorProfile.objects.filter(
            instructor_type__in=(InstructorProfile.FLYING, InstructorProfile.DUAL),
        ).select_related('user').order_by('user__first_name', 'user__last_name'),
        required=False,
        empty_label='All - Todos',
        widget=forms.Select(attrs={'class': 'ui-select'}),
    )
    students = forms.ModelChoiceField(
        label='Estudiantes',
        queryset=StudentProfile.objects.filter(
            student_phase=StudentProfile.FLYING,
        ).select_related('user').order_by('user__first_name', 'user__last_name'),
        required=False,
        empty_label='All - Todos',
        widget=forms.Select(attrs={'class': 'ui-select'}),
    )

    def clean(self):
        """Require a chronological, inclusive date range."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(
                'La fecha inicial no puede ser posterior a la fecha final.'
            )
        return cleaned_data
