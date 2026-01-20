from django import forms
from .models import VoluntaryHazardReport

class SMSVoluntaryHazardReportForm(forms.ModelForm):
    
    class Meta:
        model = VoluntaryHazardReport
        fields = [
            'is_anonymous', 'first_name', 'last_name', 'role', 'date', 'time', 'area', 'description',
        ]

        labels = {
            'is_anonymous': 'Reporte de peligro anónimo',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'role': 'Rol',
            'date': 'Fecha',
            'time': 'Hora',
            'area': 'Área',
            'description': 'Descripción',
        }

        widgets = {
            'is_anonymous': forms.RadioSelect(attrs={'class': 'radio-field'}),
            'first_name': forms.TextInput(attrs={'class': 'form-field'}),
            'last_name': forms.TextInput(attrs={'class': 'form-field'}),
            'role': forms.Select(attrs={'class': 'form-field'}),
            'date': forms.DateInput(attrs={'class': 'form-field', 'type': 'date'}),
            'time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'area': forms.Select(attrs={'class': 'form-field', 'placeholder': 'Seleccione una opción'}),
            'description': forms.Textarea(attrs={'class': 'form-field', 'rows': 10, 'placeholder': 'Mínimo 75 caracteres, máximo 1000 caracteres'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extract the 'user' argument from kwargs
        super().__init__(*args, **kwargs)
        
        if user:
            # Pre-populate form fields with user data if available
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name

    def clean(self):
        cleaned_data = super().clean()
        is_anonymous = cleaned_data.get('is_anonymous') == 'YES'

        if is_anonymous:
            cleaned_data['first_name'] = 'Anónimo'
            cleaned_data['last_name'] = 'Anónimo'
            cleaned_data['role'] = 'OTHER'

        return cleaned_data
    

class RiskEvaluationReportForm(forms.Form):
    
    report_code = forms.CharField(
        label='Código del RVP',
        widget=forms.TextInput(attrs={'class': 'form-field', 'readonly': 'readonly'})
    )
    report_date = forms.DateField(
        label='Fecha del reporte',
        widget=forms.DateInput(attrs={'class': 'form-field', 'readonly': 'readonly'})
    )
    sms_user_fullname = forms.CharField(
        label='Gerente de SMS',
        widget=forms.TextInput(attrs={'class': 'form-field'})
    )
    dir_user_fullname = forms.CharField(
        label='Director',
        widget=forms.TextInput(attrs={'class': 'form-field'})
    )
    hazard_description = forms.CharField(
        label='Descripción del peligro',
        widget=forms.Textarea(attrs={'class': 'form-field', 'rows': 10, 'placeholder': 'Máximo 1000 caracteres'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        report = kwargs.pop('report', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['sms_user_fullname'].initial = user.first_name + ' ' + user.last_name
            self.fields['dir_user_fullname'].initial = 'Elías Detto'
        
        if report:
            self.fields['report_code'].initial = report.id
            self.fields['report_date'].initial = report.date

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data