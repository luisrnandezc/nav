from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("courses/", views.courses, name="courses"),
    path("cpa/", views.cpa, name="cpa")
]
