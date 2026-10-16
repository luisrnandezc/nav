from django.urls import path
from . import fpt_views, views

app_name = "scheduler"

urlpatterns = [
    path('fpt/periods/', fpt_views.periods, name='fpt_periods'),
    path('fpt/periods/<int:period_id>/', fpt_views.period_detail, name='fpt_period_detail'),
    path('fpt/periods/<int:period_id>/delete/', fpt_views.delete_period, name='fpt_delete_period'),
    path('fpt/sessions/create/', fpt_views.create_session, name='fpt_create_session'),
    path('fpt/sessions/<int:session_id>/', fpt_views.session_detail, name='fpt_session_detail'),
    path('fpt/sessions/<int:session_id>/delete/', fpt_views.delete_session, name='fpt_delete_session'),
    path('fpt/participants/', fpt_views.participants, name='fpt_participants'),
    path('', views.staff_flight_requests_dashboard, name='staff_flight_requests_dashboard'),
    path('period/new_period/', views.create_flight_period, name='create_flight_period'),
    path('student_flight_requests_dashboard/', views.student_flight_requests_dashboard, name='student_flight_requests_dashboard'),
    path('instructor_flight_requests_dashboard/', views.instructor_flight_requests_dashboard, name='instructor_flight_requests_dashboard'),
    path('student_periods_panel/', views.create_student_flight_period_grids, name='create_student_flight_period_grids'),
    path('instructor_periods_panel/', views.create_instructor_flight_period_grids, name='create_instructor_flight_period_grids'),
    path('staff_periods_panel/', views.create_staff_flight_period_grids, name='create_staff_flight_period_grids'),
    path('flight-request/create/<int:slot_id>/', views.create_flight_request, name='create_flight_request'),
    path('flight-request/staff-create/<int:slot_id>/', views.staff_create_approved_flight_request, name='staff_create_approved_flight_request'),
    path('flight-request/approve/<int:request_id>/', views.approve_flight_request, name='approve_flight_request'),
    path('flight-request/cancel/<int:request_id>/', views.cancel_flight_request, name='cancel_flight_request'),
    path('slot/change-status/<int:slot_id>/', views.change_slot_status, name='change_slot_status'),
    path('slot/assign-instructor/<int:slot_id>/', views.assign_instructor_to_slot, name='assign_instructor_to_slot'),
    path('instructors/available/', views.get_available_instructors, name='get_available_instructors'),
    path('period/activate/<int:period_id>/', views.activate_flight_period, name='activate_flight_period'),
]
