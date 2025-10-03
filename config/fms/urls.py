from django.urls import path
from . import views

app_name = 'fms'

urlpatterns = [
     path('', views.fms_dashboard, name='fms_dashboard'),
     path('student_list/', views.student_list, name='student_list'),
     path('student_flightlog/', views.student_flightlog, name='student_flightlog'),
     path('instructor_flightlog/', views.instructor_flightlog, name='instructor_flightlog'),
     path('form_selection/', views.form_selection, name='form_selection'),
     path('submit_flight_evaluation_0_100/', views.submit_flight_evaluation_0_100, name='flight_evaluation_0_100'),
     path('submit_flight_evaluation_100_120/', views.submit_flight_evaluation_100_120, name='flight_evaluation_100_120'),
     path('submit_flight_evaluation_120_170/', views.submit_flight_evaluation_120_170, name='flight_evaluation_120_170'),
     path('submit_flight_report/', views.submit_flight_report, name='flight_report'),
     path('submit_sim_evaluation/', views.submit_sim_evaluation, name='sim_evaluation'),
     path('api/get_student_data/', views.get_student_data, name='get_student_data'),
     path('pdf_download_waiting_page/<str:form_type>/<int:evaluation_id>/', views.pdf_download_waiting_page, name='pdf_download_waiting_page'),
     path('download_pdf/<str:form_type>/<int:evaluation_id>/', views.download_pdf, name='download_pdf'),
]