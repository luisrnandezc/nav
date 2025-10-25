from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
from django.urls import reverse_lazy
from .views import CustomPasswordChangeView

app_name = 'accounts'

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('role-selection/', views.role_selection, name='role_selection'),
    path('select-role/<str:role>/', views.select_role, name='select_role'),
    path('password-change/', CustomPasswordChangeView.as_view(success_url=reverse_lazy('accounts:password_change_done')), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done')
]