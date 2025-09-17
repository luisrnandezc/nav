from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.transactions_dashboard, name='transactions_dashboard'),
    path('add/', views.add_transaction, name='add_transaction'),
    path('confirm/<int:transaction_id>/', views.confirm_transaction, name='confirm_transaction'),
    path('unconfirm/<int:transaction_id>/', views.unconfirm_transaction, name='unconfirm_transaction'),
]