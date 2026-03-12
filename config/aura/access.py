from accounts.models import StudentProfile
from accounts.role_utils import resolve_active_role


def get_aura_capabilities(request):
    """Return AURA capabilities for the current user and active role."""
    active_role = resolve_active_role(request.user, request.session.get("selected_role"))
    student_profile = getattr(request.user, "student_profile", None)
    is_flying_student = (
        student_profile is not None
        and student_profile.student_phase == StudentProfile.FLYING
    )

    capabilities = {
        "active_role": active_role,
        "can_view_own_review": active_role == "STUDENT" and is_flying_student,
        "can_view_all_reviews": active_role in {"INSTRUCTOR", "STAFF"},
        "can_download_pdf": active_role in {"INSTRUCTOR", "STAFF"},
        "can_update_review": (
            active_role == "STAFF"
            and request.user.has_perm("accounts.can_update_aura_reviews")
        ),
    }

    capabilities["can_access_aura"] = (
        capabilities["can_view_own_review"] or capabilities["can_view_all_reviews"]
    )

    return capabilities
