from django.urls import path
from . import views

app_name = "scheduler"

urlpatterns = [
    path('', views.flight_requests_dashboard, name='flight_requests_dashboard'),
    path('period/new/', views.create_training_period, name='create_training_period'),
    path('period/calendar/', views.training_period_calendar, name='training_period_calendar'),
]