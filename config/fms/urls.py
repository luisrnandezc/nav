from django.urls import path
from . import views

app_name = 'fms'

urlpatterns = [
    path('fms/form_selection/', views.form_selection, name='form_selection'),
    path('fms/submit_flight_evaluation/', views.submit_flight_evaluation, name='flight_evaluation'),
]