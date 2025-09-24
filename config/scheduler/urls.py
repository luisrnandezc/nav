from django.urls import path
from . import views

app_name = "scheduler"

urlpatterns = [
    path('', views.flight_requests_dashboard, name='flight_requests_dashboard'),
    path('period/new/', views.create_training_period, name='create_training_period'),
    path('period/calendar/', views.create_training_period_grids, name='create_training_period_grids'),
    path('scheduler/student_dashboard/', views.student_scheduler_dashboard, name='student_scheduler_dashboard'),
]