from django.urls import path
from . import views

app_name = 'academic'

urlpatterns = [
    path('academic/', views.submit_student_grade, name='student_grade'),
]