from django.urls import path
from . import views
from .debug_email import email_debug_view

app_name = 'sms'

urlpatterns = [
    # Define your URL patterns here
    # path('', views.index, name='index'),
    path('email-debug/', email_debug_view, name='email_debug'),
]