from django import forms
from .models import SubjectEdition, StudentGrade, SubjectEditionGradingComponent
from accounts.models import User

class StudentGradeForm(forms.ModelForm):
    """Form for submitting student grades"""
    class Meta:
        model = StudentGrade
        fields = ['subject_edition', 'component', 'student', 'grade', 'test_type']
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
            self.fields['component'].queryset = SubjectEditionGradingComponent.objects.filter(
                subject_edition__instructor=self.instructor
            ).select_related('subject_edition', 'subject_edition__subject_type').order_by(
                'subject_edition_id', 'order', 'code'
            )
            
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
            self.fields['component'].widget.attrs.update({
                'class': 'form-field component-select',
            })

    def clean(self):
        cleaned_data = super().clean()
        subject_edition = cleaned_data.get('subject_edition')
        student = cleaned_data.get('student')
        component = cleaned_data.get('component')

        if subject_edition and not component:
            comps = list(subject_edition.grading_components.order_by('order', 'code'))
            if len(comps) == 1:
                cleaned_data['component'] = comps[0]
                component = comps[0]
            elif len(comps) == 0:
                raise forms.ValidationError(
                    'Esta edición de materia no tiene componentes de calificación configurados. '
                    'Contacte a administración.'
                )

        if subject_edition and component and component.subject_edition_id != subject_edition.id:
            raise forms.ValidationError(
                {'component': 'El componente no corresponde a la edición de materia seleccionada.'}
            )

        if subject_edition and student:
            if not subject_edition.students.filter(id=student.id).exists():
                raise forms.ValidationError(
                    'El estudiante seleccionado no está inscrito en esta materia'
                )

        return cleaned_data