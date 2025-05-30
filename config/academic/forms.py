from django import forms
from .models import SubjectEdition, StudentGrade
from accounts.models import User

class StudentGradeForm(forms.ModelForm):
    """Form for submitting student grades"""
    class Meta:
        model = StudentGrade
        fields = ['subject_edition', 'student', 'grade', 'test_type']

    def __init__(self, *args, **kwargs):
        self.instructor = kwargs.pop('instructor', None)
        super().__init__(*args, **kwargs)
        
        if self.instructor:
            # Filter subject editions to only show those assigned to this instructor
            self.fields['subject_edition'].queryset = SubjectEdition.objects.filter(
                instructor=self.instructor
            ).order_by('subject_type__name')
            
            # If we have POST data and a subject_edition, set the student queryset
            if self.data.get('subject_edition'):
                try:
                    subject_edition = SubjectEdition.objects.get(
                        id=self.data.get('subject_edition'),
                        instructor=self.instructor
                    )
                    self.fields['student'].queryset = subject_edition.students.all().order_by('first_name', 'last_name')
                except SubjectEdition.DoesNotExist:
                    self.fields['student'].queryset = User.objects.none()
            else:
                # Initially set student choices to empty
                self.fields['student'].queryset = User.objects.none()
            
            # Add classes and data attributes for all fields
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
        test_type = cleaned_data.get('test_type')
        
        if subject_edition and student and test_type:
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
            
            # Check for duplicate grade
            if StudentGrade.objects.filter(
                subject_edition=subject_edition,
                student=student,
                test_type=test_type
            ).exists():
                raise forms.ValidationError(
                    'Ya existe una nota para este estudiante en esta materia con el mismo tipo de examen.'
                )
        
        return cleaned_data
