from django.urls import path
from . import views

app_name = 'fms'

urlpatterns = [
    path('fms/', views.submit_flight_evaluation, name='flight_evaluation'),
]