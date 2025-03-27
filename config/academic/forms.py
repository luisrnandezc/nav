from django import forms
from .models import Subject, Enrollment, Grade

# Assigning Instructor to a Subject
class InstructorAssignmentForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['instructor']

# Enrolling Student in Subject
class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['student', 'subject']

# Grade Submission by Instructor
class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['student', 'subject', 'score']
