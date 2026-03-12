from django.urls import path

from . import views

app_name = "aura"

urlpatterns = [
    path("", views.aura_home, name="home"),
    path("my-review/", views.my_global_review, name="my_global_review"),
    path("students/", views.student_review_list, name="student_review_list"),
    path(
        "student/<int:student_profile_id>/",
        views.student_global_review,
        name="student_global_review",
    ),
    path(
        "student/<int:student_profile_id>/download_pdf/",
        views.download_global_review_pdf,
        name="download_global_review_pdf",
    ),
    path(
        "student/<int:student_profile_id>/refresh/",
        views.refresh_global_review,
        name="refresh_global_review",
    ),
]

