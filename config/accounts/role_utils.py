ROLE_LABELS = {
    "STUDENT": "Estudiante",
    "INSTRUCTOR": "Instructor",
    "STAFF": "Staff",
}

ROLE_PRIORITY = ["STAFF", "INSTRUCTOR", "STUDENT"]


def has_profile(user, profile_name):
    """Safely check whether the user has a given profile relation."""
    try:
        return hasattr(user, profile_name) and getattr(user, profile_name)
    except Exception:
        return False


def get_available_roles(user):
    """Return the roles the current user can activate."""
    available_roles = []

    if has_profile(user, "student_profile"):
        available_roles.append("STUDENT")

    if has_profile(user, "instructor_profile"):
        available_roles.append("INSTRUCTOR")

    if has_profile(user, "staff_profile"):
        available_roles.append("STAFF")

    return available_roles


def get_default_role(user):
    """Return the default role using the shared priority order."""
    available_roles = get_available_roles(user)

    for role in ROLE_PRIORITY:
        if role in available_roles:
            return role

    return getattr(user, "role", None)


def resolve_active_role(user, selected_role):
    """Use the session role when valid, otherwise fall back to the default role."""
    available_roles = get_available_roles(user)

    if selected_role in available_roles:
        return selected_role

    return get_default_role(user)
