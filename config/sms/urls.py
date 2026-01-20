from django.urls import path
from . import views

app_name = 'sms'

urlpatterns = [
    path('', views.sms_dashboard, name='sms_dashboard'),
    path('vhr_dashboard/', views.vhr_dashboard, name='vhr_dashboard'),
    path('vhr_form/', views.vhr_form, name='vhr_form'),
    path('vhr_action_panel/<int:report_id>/', views.vhr_action_panel, name='vhr_action_panel'),
    path('voluntary_hazard_report/<int:report_id>/register/', views.register_vhr, name='register_vhr'),
    path('voluntary_hazard_report/<int:report_id>/download_pdf/', views.download_vhr_pdf, name='download_vhr_pdf'),
    path('voluntary_hazard_report/<int:report_id>/process/', views.process_vhr, name='process_vhr'),
    path('voluntary_hazard_report/<int:report_id>/validity/update/', views.update_validity, name='update_validity'),
    path('voluntary_hazard_report/<int:report_id>/risk/<str:risk_key>/delete/', views.delete_risk, name='delete_risk'),
    path('voluntary_hazard_report/<int:report_id>/risk/<str:risk_key>/evaluation/update/', views.update_risk_evaluation, name='update_risk_evaluation'),
    path('voluntary_hazard_report/<int:report_id>/risk/<str:risk_key>/actions/<int:action_index>/delete/', views.delete_action, name='delete_action'),
    path('voluntary_hazard_report/<int:report_id>/risk/add/', views.add_risk, name='add_risk'),
    path('voluntary_hazard_report/<int:report_id>/risk/<str:risk_key>/actions/add/', views.add_action, name='add_action'),
    path('vhr_processed_panel/<int:report_id>/', views.vhr_processed_panel, name='vhr_processed_panel'),
    path('risk/<int:risk_id>/', views.risk_detail, name='risk_detail'),
    path('action/<int:action_id>/', views.action_detail, name='action_detail'),
    path('action/<int:action_id>/update_notes/', views.update_action_notes, name='update_action_notes'),
    path('action/<int:action_id>/update_due_date/', views.update_action_due_date, name='update_action_due_date'),
    path('action/<int:action_id>/update_responsible/', views.update_action_responsible, name='update_action_responsible'),
    path('action/<int:action_id>/mark_completed/', views.mark_action_completed, name='mark_action_completed'),
    path('action/<int:action_id>/evidence/add/', views.add_evidence, name='add_evidence'),
    path('action/<int:action_id>/evidence/<int:evidence_id>/delete/', views.delete_evidence, name='delete_evidence'),
    path('rer_form/<int:report_id>/', views.rer_form, name='rer_form'),
    path('rer/<int:report_id>/generate_rer_pdf/', views.generate_rer_pdf, name='generate_rer_pdf'),
]