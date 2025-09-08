from django.urls import path
from . import views

app_name = 'sms'

urlpatterns = [
    path('', views.main_sms, name='main_sms'),
    path('voluntary_report/', views.voluntary_report, name='voluntary_report'),
    path('report_list/', views.report_list, name='report_list'),
    path('report_detail/<int:report_id>/', views.report_detail, name='report_detail'),
]