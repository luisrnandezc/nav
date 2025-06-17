from django.urls import path
from . import views

app_name = 'fms'

urlpatterns = [
    path('fms/form_selection/', views.form_selection, name='form_selection'),
    path('fms/submit_flight_evaluation_0_100/', views.submit_flight_evaluation_0_100, name='flight_evaluation_0_100'),
    path('fms/submit_flight_evaluation_100_120/', views.submit_flight_evaluation_100_120, name='flight_evaluation_100_120'),
]