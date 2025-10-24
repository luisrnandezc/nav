from django.urls import path
from . import views

app_name = 'sms'

urlpatterns = [
    path('', views.main_sms, name='main_sms'),
    path('voluntary_report/', views.voluntary_report, name='voluntary_report'),
    path('report_list/', views.report_list, name='report_list'),
    path('report_detail/<int:report_id>/', views.report_detail, name='report_detail'),
    
    # Risk Management URLs
    path('report/<int:report_id>/risk/<int:item_index>/delete/', views.delete_risk_item, name='delete_risk_item'),
    path('report/<int:report_id>/risk/add/', views.add_risk_item, name='add_risk_item'),
    
    # Recommendation Management URLs
    path('report/<int:report_id>/recommendation/<int:item_index>/delete/', views.delete_recommendation_item, name='delete_recommendation_item'),
    path('report/<int:report_id>/recommendation/add/', views.add_recommendation_item, name='add_recommendation_item'),
    
    # Action Management URLs
    path('report/<int:report_id>/create_actions/', views.create_actions_from_recommendations, name='create_actions'),
]