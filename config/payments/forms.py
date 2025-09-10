from django import forms
from django.utils import timezone
from .models import StudentPayment
from accounts.models import StudentProfile


class StudentPaymentForm(forms.ModelForm):
    """Form for adding new student payments."""
    
    class Meta:
        model = StudentPayment
        fields = [
            'student_profile',
            'amount',
            'type',
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
            'type': 'Tipo de Pago',
            'date_added': 'Fecha de Pago',
            'confirmed': 'Confirmar Pago',
            'notes': 'Notas'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['student_profile'].queryset = StudentProfile.objects.select_related('user').order_by('user__last_name')
        self.fields['date_added'].initial = timezone.now().date()
        
        # Hide confirmed field if user doesn't have permission
        if not self.user or not hasattr(self.user, 'staff_profile') or not self.user.staff_profile.can_confirm_payments:
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
            raise forms.ValidationError('La fecha de pago no puede ser futura.')
        return date_added
