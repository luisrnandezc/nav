from django.urls import path

from . import views

app_name = "aura"

urlpatterns = [
    path("staff/", views.staff_aura_dashboard, name="staff_aura_dashboard"),
    path(
        "staff/student/<int:student_profile_id>/",
        views.staff_student_global_review,
        name="staff_student_global_review",
    ),
    path(
        "staff/student/<int:student_profile_id>/download_pdf/",
        views.download_global_review_pdf,
        name="download_global_review_pdf",
    ),
]

