from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('student_logs/', views.student_logs, name='student_logs'),
    path('instructor_logs/', views.instructor_logs, name='instructor_logs'),
]