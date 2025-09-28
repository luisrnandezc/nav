from django import forms
from django.forms.widgets import DateInput
from .models import FlightPeriod
from fleet.models import Aircraft


class CreateFlightPeriodForm(forms.ModelForm):
    class Meta:
        model = FlightPeriod
        fields = [
            'start_date',
            'end_date',
            'aircraft',
            'is_active',
        ]
        widgets = {
            'start_date': DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'Seleccione un lunes'
            }),
            'end_date': DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'Seleccione un domingo'
            }),
            'aircraft': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Seleccione aeronave'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            })
        }
        labels = {
            'start_date': 'Inicio (debe ser lunes):',
            'end_date': 'Cierre (debe ser domingo):',
            'aircraft': 'Aeronave:',
            'is_active': 'Publicar:'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            if field_name != 'is_active' and field_name != 'aircraft':
                field.widget.attrs.update({
                    'class': 'form-input'
                })
        
        # Set minimum date to today for start_date
        from datetime import date
        self.fields['start_date'].widget.attrs['min'] = date.today().strftime('%Y-%m-%d')
        
        # Set minimum date to start_date for end_date (will be updated via JavaScript)
        self.fields['end_date'].widget.attrs['min'] = date.today().strftime('%Y-%m-%d')

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date:
            # Check if start_date is a Monday (weekday() returns 0 for Monday)
            if start_date.weekday() != 0:
                self.add_error('start_date', 'La fecha de inicio debe ser un lunes.')
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        if end_date:
            # Check if end_date is a Sunday (weekday() returns 6 for Sunday)
            if end_date.weekday() != 6:
                self.add_error('end_date', 'La fecha de cierre debe ser un domingo.')
        return end_date

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if end_date < start_date:
                self.add_error('end_date', 'La fecha de cierre debe ser posterior a la fecha de inicio.')

        return cleaned_data