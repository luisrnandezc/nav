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
            'test_type': forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        self.instructor = kwargs.pop('instructor', None)
        super().__init__(*args, **kwargs)
        
        if self.instructor:
            # Filter subject editions to only show those assigned to this instructor
            self.fields['subject_edition'].queryset = SubjectEdition.objects.filter(
                instructor=self.instructor
            ).order_by('subject_type__name')
            
            # Initially set student choices to empty
            self.fields['student'].queryset = User.objects.none()
            
            # Add a data attribute to store the URL for dynamic student loading
            self.fields['subject_edition'].widget.attrs.update({
                'class': 'subject-edition-select',
                'data-url': '/academic/ajax/load-students/'  # You'll need to create this URL
            })
            
            # Add class to student field for dynamic updates
            self.fields['student'].widget.attrs.update({
                'class': 'student-select'
            })

    def clean(self):
        cleaned_data = super().clean()
        subject_edition = cleaned_data.get('subject_edition')
        student = cleaned_data.get('student')
        
        if subject_edition and student:
            # Check if student is enrolled in the subject
            if not subject_edition.students.filter(id=student.id).exists():
                raise forms.ValidationError(
                    'El estudiante seleccionado no está inscrito en esta materia'
                )
            
            # Check if instructor is assigned to the subject
            if subject_edition.instructor != self.instructor:
                raise forms.ValidationError(
                    'No está autorizado para calificar esta materia'
                )
        
        return cleaned_data
