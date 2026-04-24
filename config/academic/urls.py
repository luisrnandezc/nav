from django.urls import path
from . import views

app_name = 'academic'

urlpatterns = [
    path('submit-grade/', views.submit_student_grade, name='submit_grade'),
    path('ajax/load-students/', views.load_students, name='ajax_load_students'),
    path('ajax/load-grading-components/', views.load_grading_components, name='ajax_load_grading_components'),
    path('grade_logs/', views.grade_logs, name='grade_logs'),
    path('instructor-grades-dashboard/', views.instructor_grades_dashboard, name='instructor_grades_dashboard'),
]