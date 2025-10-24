from django import forms
from .models import VoluntaryReport, ReportAnalysis

class SMSVoluntaryReportForm(forms.ModelForm):
    
    class Meta:
        model = VoluntaryReport
        fields = [
            'is_anonymous', 'first_name', 'last_name', 'role', 'date', 'time', 'area', 'description',
        ]

        labels = {
            'is_anonymous': 'Reporte anónimo',
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

class SMSAnalysisEditForm(forms.ModelForm):
    """Form for editing AI analysis results by SMS managers"""
    
    class Meta:
        model = ReportAnalysis
        fields = [
            'is_valid', 'severity', 'probability'
        ]
        
        labels = {
            'is_valid': 'Validez del Reporte',
            'severity': 'Nivel de Severidad',
            'probability': 'Nivel de Probabilidad', 
        }
        
        widgets = {
            'is_valid': forms.Select(attrs={'class': 'form-field'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make all fields not required for partial updates
        for field_name, field in self.fields.items():
            field.required = False
        
        # Override severity field with proper choices and widget
        self.fields['severity'] = forms.ChoiceField(
            choices=[
                ('', 'Seleccione severidad'),
                ('A', 'A - Catastrófico'),
                ('B', 'B - Peligroso'),
                ('C', 'C - Grave'),
                ('D', 'D - Leve'),
                ('E', 'E - Insignificante'),
            ],
            widget=forms.Select(attrs={'class': 'form-field'}),
            label='Nivel de Severidad',
            required=False
        )
        
        # Override probability field with proper choices and widget
        self.fields['probability'] = forms.ChoiceField(
            choices=[
                ('', 'Seleccione probabilidad'),
                ('1', '1 - Sumamente improbable'),
                ('2', '2 - Improbable'),
                ('3', '3 - Remoto'),
                ('4', '4 - Ocasional'),
                ('5', '5 - Frecuente'),
            ],
            widget=forms.Select(attrs={'class': 'form-field'}),
            label='Nivel de Probabilidad',
            required=False
        )
    
    def save(self, commit=True):
        """Override save to automatically generate the value field"""
        instance = super().save(commit=False)
        
        # Auto-generate value from severity + probability
        if instance.severity and instance.probability:
            instance.value = f"{instance.severity}{instance.probability}"
        
        if commit:
            instance.save()
        
        return instance