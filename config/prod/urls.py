from django.urls import path

from . import views


app_name = 'prod'

urlpatterns = [
    path('', views.production_panel, name='production_panel'),
]
