from django.urls import path
from . import views

app_name = 'academic'

urlpatterns = [
    path('submit-grade/', views.submit_student_grade, name='submit_grade'),
    path('ajax/load-students/', views.load_students, name='ajax_load_students'),
    path('grade_logs/', views.grade_logs, name='grade_logs'),
]