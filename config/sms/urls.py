from django.urls import path
from . import views

app_name = 'sms'

urlpatterns = [
    path('', views.sms_dashboard, name='sms_dashboard'),
    path('voluntary_hazard_report/', views.voluntary_hazard_report, name='voluntary_hazard_report'),
    path('voluntary_hazard_report/<int:report_id>/', views.voluntary_hazard_report_detail, name='voluntary_hazard_report_detail'),
    path('voluntary_hazard_report/<int:report_id>/register/', views.register_rvp, name='register_rvp'),
    path('voluntary_hazard_report/<int:report_id>/download_pdf/', views.download_rvp_pdf, name='download_rvp_pdf'),
    path('voluntary_hazard_report/<int:report_id>/create_mmrs/', views.create_mmrs, name='create_mmrs'),
    path('voluntary_hazard_report/<int:report_id>/validity/update/', views.update_validity, name='update_validity'),
    path('voluntary_hazard_report/<int:report_id>/risk/<str:risk_key>/delete/', views.delete_risk, name='delete_risk'),
    path('voluntary_hazard_report/<int:report_id>/risk/<str:risk_key>/evaluation/update/', views.update_risk_evaluation, name='update_risk_evaluation'),
    path('voluntary_hazard_report/<int:report_id>/risk/<str:risk_key>/actions/<int:action_index>/delete/', views.delete_action, name='delete_action'),
    path('voluntary_hazard_report/<int:report_id>/risk/add/', views.add_risk, name='add_risk'),
    path('voluntary_hazard_report/<int:report_id>/risk/<str:risk_key>/actions/add/', views.add_action, name='add_action'),
]