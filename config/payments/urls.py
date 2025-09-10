from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payments_dashboard, name='payments_dashboard'),
    path('add/', views.add_payment, name='add_payment'),
    path('confirm/<int:payment_id>/', views.confirm_payment, name='confirm_payment'),
    path('unconfirm/<int:payment_id>/', views.unconfirm_payment, name='unconfirm_payment'),
]