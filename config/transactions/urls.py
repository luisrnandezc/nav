from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.transactions_dashboard, name='transactions_dashboard'),
    path('add/', views.add_transaction, name='add_transaction'),
    path('add-fuel-transaction/', views.add_fuel_transaction, name='add_fuel_transaction'),
    path('update-fuel-consumed/', views.update_fuel_consumed, name='update_fuel_consumed'),
    path('detail/<int:transaction_id>/', views.transaction_detail, name='transaction_detail'),
    path('confirm/<int:transaction_id>/', views.confirm_transaction, name='confirm_transaction'),
    path('unconfirm/<int:transaction_id>/', views.unconfirm_transaction, name='unconfirm_transaction'),
]