from django.urls import path
from . import views

app_name = "scheduler"

urlpatterns = [
    path('', views.staff_flight_requests_dashboard, name='staff_flight_requests_dashboard'),
    path('period/new_period/', views.create_flight_period, name='create_flight_period'),
    path('student_flight_requests_dashboard/', views.student_flight_requests_dashboard, name='student_flight_requests_dashboard'),
    path('student_periods_panel/', views.create_student_flight_period_grids, name='create_student_flight_period_grids'),
    path('staff_periods_panel/', views.create_staff_flight_period_grids, name='create_staff_flight_period_grids'),
    path('flight-request/create/<int:slot_id>/', views.create_flight_request, name='create_flight_request'),
    path('flight-request/approve/<int:request_id>/', views.approve_flight_request, name='approve_flight_request'),
    path('flight-request/cancel/<int:request_id>/', views.cancel_flight_request, name='cancel_flight_request'),
    path('slot/change-status/<int:slot_id>/', views.change_slot_status, name='change_slot_status'),
    path('slot/assign-instructor/<int:slot_id>/', views.assign_instructor_to_slot, name='assign_instructor_to_slot'),
    path('instructors/available/', views.get_available_instructors, name='get_available_instructors'),
    path('period/activate/<int:period_id>/', views.activate_flight_period, name='activate_flight_period'),
]