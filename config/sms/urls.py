from django.urls import path
from . import views

app_name = 'sms'

urlpatterns = [
    path('', views.sms_dashboard, name='sms_dashboard'),
    path('voluntary_hazard_report/', views.voluntary_hazard_report, name='voluntary_hazard_report'),
    path('voluntary_hazard_report/<int:report_id>/', views.voluntary_hazard_report_detail, name='voluntary_hazard_report_detail'),
    path('voluntary_hazard_report/<int:report_id>/risk/<str:risk_key>/delete/', views.delete_risk, name='delete_risk'),
    path('voluntary_hazard_report/<int:report_id>/risk/<str:risk_key>/actions/<int:action_index>/delete/', views.delete_action, name='delete_action'),
]