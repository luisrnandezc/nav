from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
from accounts.forms import LoginForm

app_name = 'accounts'

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout')
]