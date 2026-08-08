from django import forms
from django.forms import modelformset_factory

from .models import Risk, RiskEvaluationReport, VoluntaryHazardReport

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
    

class RiskEvaluationReportForm(forms.ModelForm):
    report_code = forms.CharField(
        label='Código del RVP',
        disabled=True,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-field'}),
    )
    class Meta:
        model = RiskEvaluationReport
        fields = [
            'registration_date',
            'sms_user_fullname',
            'dir_user_fullname',
            'hazard_description',
            'hazard_source',
            'hazard_type',
            'hazard_area',
            'selected_risk',
            'hazard_causes',
            'defenses',
        ]
        widgets = {
            'registration_date': forms.DateInput(attrs={'class': 'form-field'}),
            'sms_user_fullname': forms.TextInput(attrs={'class': 'form-field'}),
            'dir_user_fullname': forms.TextInput(attrs={'class': 'form-field'}),
            'hazard_description': forms.Textarea(attrs={
                'class': 'form-field',
                'rows': 10,
                'placeholder': 'Descripción del peligro (máximo 300 caracteres)',
            }),
            'hazard_source': forms.Select(attrs={'class': 'form-field'}),
            'hazard_type': forms.Select(attrs={'class': 'form-field'}),
            'hazard_area': forms.Select(attrs={'class': 'form-field'}),
            'selected_risk': forms.RadioSelect(attrs={'class': 'risk-radio-input'}),
            'hazard_causes': forms.Textarea(attrs={
                'class': 'form-field',
                'placeholder': 'Causas posibles (máximo 1000 caracteres)',
            }),
            'defenses': forms.Textarea(attrs={
                'class': 'form-field',
                'placeholder': 'Máximo 500 caracteres',
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        report = kwargs.pop('report', None)
        super().__init__(*args, **kwargs)

        if report is None:
            raise ValueError('RiskEvaluationReportForm requires a VHR report.')

        self.fields['report_code'].initial = report.code or f'RVP {report.id}'
        self.fields['registration_date'].disabled = True
        self.fields['selected_risk'].queryset = report.risks.all()
        self.fields['selected_risk'].label_from_instance = (
            lambda risk: (
                f"({risk.pre_evaluation_severity}{risk.pre_evaluation_probability}) "
                f"{risk.description}"
            )
        )

        if not self.instance.pk:
            self.fields['registration_date'].initial = report.date
            self.fields['hazard_description'].initial = report.description[:300]
            self.fields['hazard_source'].initial = 'VHR'
            self.fields['hazard_area'].initial = report.area

            if user:
                self.fields['sms_user_fullname'].initial = (
                    f'{user.first_name} {user.last_name}'.strip()
                )
                self.fields['dir_user_fullname'].initial = 'Elías Detto'


class RiskResidualReviewForm(forms.ModelForm):
    """Allow the SMS coordinator to review SARA's result for one risk."""

    class Meta:
        model = Risk
        fields = [
            'post_evaluation_severity',
            'post_evaluation_probability',
            'post_evaluation_justification',
        ]
        labels = {
            'post_evaluation_severity': 'Severidad residual',
            'post_evaluation_probability': 'Probabilidad residual',
            'post_evaluation_justification': 'Justificación de SARA',
        }
        widgets = {
            'post_evaluation_severity': forms.Select(attrs={
                'class': 'risk-evaluation-select',
            }),
            'post_evaluation_probability': forms.Select(attrs={
                'class': 'risk-evaluation-select',
            }),
            'post_evaluation_justification': forms.Textarea(attrs={
                'class': 'action-form-textarea residual-justification',
                'rows': 5,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # A reviewed result must contain a real matrix value, never the "-" option.
        self.fields['post_evaluation_severity'].choices = Risk.SEVERITY_CHOICES[1:]
        self.fields['post_evaluation_probability'].choices = Risk.PROBABILITY_CHOICES[1:]
        self.fields['post_evaluation_justification'].required = True


RiskResidualReviewFormSet = modelformset_factory(
    Risk,
    form=RiskResidualReviewForm,
    extra=0,
)
