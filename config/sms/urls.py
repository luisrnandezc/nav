from django.urls import path
from . import views

app_name = 'sms'

urlpatterns = [
    path('voluntary_report/', views.voluntary_report, name='voluntary_report'),
]