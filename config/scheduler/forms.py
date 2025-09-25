from django import forms
from django.forms.widgets import DateInput
from .models import TrainingPeriod
from fleet.models import Aircraft


class CreateTrainingPeriodForm(forms.ModelForm):
    class Meta:
        model = TrainingPeriod
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
                'placeholder': 'Seleccione fecha de inicio'
            }),
            'end_date': DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'Seleccione fecha de cierre'
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
            'start_date': 'Fecha de inicio:',
            'end_date': 'Fecha de cierre:',
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

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        aircraft = cleaned_data.get('aircraft')

        if start_date and end_date:
            if end_date < start_date:
                self.add_error('end_date', 'La fecha de cierre debe ser posterior a la fecha de inicio.')
            
            # Check if period is too long (more than 6 months)
            if (end_date - start_date).days > 180:
                self.add_error('end_date', 'El período no puede ser mayor a 6 meses.')
            
            # Check if period is too short (less than 1 week)
            if (end_date - start_date).days + 1 < 7:
                self.add_error('end_date', 'El período debe ser de al menos 7 días.')
            
            # Check if duration is a multiple of 5
            duration = (end_date - start_date).days + 1
            if duration % 5 != 0:
                self.add_error('end_date', 'La duración del período debe ser un múltiplo de 5 días (5, 10, 15, 20, etc.).')
            
            # Check for existing slots in the date range
            if aircraft and start_date and end_date:
                from scheduler.models import FlightSlot

                existing_slots = FlightSlot.objects.filter(
                    aircraft=aircraft,
                    date__range=[start_date, end_date]
                ).exists()
                
                if existing_slots:
                    self.add_error('end_date', f'Ya existen slots creados para la aeronave {aircraft.registration} en el rango de fechas seleccionado. Por favor, seleccione un rango de fechas diferente.')
        
        if aircraft and aircraft not in Aircraft.objects.filter(is_active=True, is_available=True):
            self.add_error('aircraft', 'La aeronave no está activa o disponible.')

        return cleaned_data


