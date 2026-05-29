from django.urls import path

from . import views

app_name = 'maintenance'

urlpatterns = [
    path('', views.discrepancy_reports_panel, name='discrepancy_reports_panel'),
    path('discrepancies/', views.discrepancy_reports_panel, name='discrepancy_reports'),
]
