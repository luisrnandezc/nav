"""FPT permission policy for future server-side entry points.

Management includes viewing. A permission never enables student self-booking.
School staff includes instructors, consistent with the existing role model.
"""


def can_manage_fpt_schedule(user):
    return bool(
        user.is_authenticated and user.is_active
        and user.role in ('STAFF', 'INSTRUCTOR')
        and user.has_perm('scheduler.manage_fpt_schedule')
    )


def can_view_fpt_schedule(user):
    return bool(
        user.is_authenticated and user.is_active
        and user.role in ('STAFF', 'INSTRUCTOR')
        and (user.has_perm('scheduler.view_fpt_schedule') or can_manage_fpt_schedule(user))
    )
