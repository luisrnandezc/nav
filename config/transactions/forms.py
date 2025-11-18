from django import forms
from django.utils import timezone
from decimal import Decimal
from .models import StudentTransaction
from accounts.models import StudentProfile
from fms.models import FlightEvaluation0_100, FlightEvaluation100_120, FlightEvaluation120_170


class StudentTransactionForm(forms.ModelForm):
    """Form for adding new student transactions."""
    
    class Meta:
        model = StudentTransaction
        fields = [
            'student_profile',
            'amount',
            'type',
            'category',
            'date_added',
            'confirmed',
            'notes'
        ]
        widgets = {
            'student_profile': forms.Select(attrs={
                'class': 'form-field',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-field',
                'step': '0.01',
                'required': True
            }),
            'type': forms.Select(attrs={
                'class': 'form-field',
                'required': True
            }),
            'category': forms.Select(attrs={
                'class': 'form-field',
                'required': True
            }),
            'date_added': forms.DateInput(attrs={
                'class': 'form-field',
                'type': 'date',
                'required': True
            }),
            'confirmed': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-field',
                'rows': 3,
                'placeholder': 'Notas adicionales (opcional)'
            })
        }
        labels = {
            'student_profile': 'Estudiante',
            'amount': 'Monto ($)',
            'type': 'Tipo de Transacción',
            'category': 'Categoría de Transacción',
            'date_added': 'Fecha de Transacción',
            'confirmed': 'Confirmar Transacción',
            'notes': 'Notas'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['student_profile'].queryset = StudentProfile.objects.select_related('user').order_by('user__last_name')
        self.fields['date_added'].initial = timezone.now().date()
        
        # Hide confirmed field if user doesn't have permission
        if not self.user or not self.user.has_perm('accounts.can_confirm_transactions'):
            self.fields.pop('confirmed', None)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None:
            if amount == 0:
                raise forms.ValidationError('El monto no puede ser 0.')
            if abs(amount) > 50000:
                raise forms.ValidationError('El monto no puede exceder $50,000.')
        return amount

    def clean_date_added(self):
        date_added = self.cleaned_data.get('date_added')
        if date_added and date_added > timezone.now().date():
            raise forms.ValidationError('La fecha de transacción no puede ser futura.')
        return date_added

class FuelTransactionSearchForm(forms.Form):
    """Simple form to search for student evaluations with missing fuel data."""
    
    student_national_id = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-field',
            'required': True,
            'placeholder': 'Ej: 12345678'
        }),
        label='ID del Estudiante'
    )
    
    def clean_student_national_id(self):
        student_id = self.cleaned_data.get('student_national_id')
        if student_id:
            from accounts.models import StudentProfile
            try:
                StudentProfile.objects.get(user__national_id=student_id)
            except StudentProfile.DoesNotExist:
                raise forms.ValidationError(f'No se encontró un estudiante con ID nacional {student_id}.')
        return student_id