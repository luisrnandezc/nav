from django.urls import path
from . import views

app_name = 'sms'

urlpatterns = [
    path('', views.main_sms, name='main_sms'),
    path('voluntary_hazard_report/', views.voluntary_hazard_report, name='voluntary_hazard_report'),
]