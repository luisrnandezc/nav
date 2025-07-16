from django import forms
from .models import SubjectEdition, StudentGrade
from accounts.models import User

class StudentGradeForm(forms.ModelForm):
    """Form for submitting student grades"""
    class Meta:
        model = StudentGrade
        fields = ['subject_edition', 'student', 'grade', 'test_type']
        widgets = {
            'grade': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': 0.1}),
        }

    def __init__(self, *args, **kwargs):
        self.instructor = kwargs.pop('instructor', None)
        super().__init__(*args, **kwargs)
        
        if self.instructor:
            # Filter subject editions to only show those assigned to this instructor
            self.fields['subject_edition'].queryset = SubjectEdition.objects.filter(
                instructor=self.instructor
            ).order_by('subject_type__name')
            
            # Set student queryset to all students initially (JavaScript will handle filtering)
            self.fields['student'].queryset = User.objects.filter(role='STUDENT').order_by('first_name', 'last_name')
            
            # Add classes for JavaScript
            self.fields['subject_edition'].widget.attrs.update({
                'class': 'form-field subject-edition-select',
                'data-url': '/academic/ajax/load-students/'
            })
            
            self.fields['student'].widget.attrs.update({
                'class': 'form-field student-select'
            })
            
            self.fields['grade'].widget.attrs.update({
                'class': 'form-field',
                'min': 0,
                'max': 100,
                'step': 0.1
            })
            
            self.fields['test_type'].widget.attrs.update({
                'class': 'form-field'
            })

    def clean(self):
        cleaned_data = super().clean()
        subject_edition = cleaned_data.get('subject_edition')
        student = cleaned_data.get('student')
        
        # Only validate if both fields are provided
        if subject_edition and student:
            # Check if student is enrolled in the subject (business rule)
            if not subject_edition.students.filter(id=student.id).exists():
                raise forms.ValidationError(
                    'El estudiante seleccionado no está inscrito en esta materia'
                )
        
        return cleaned_data