from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from accounts.role_utils import (
    ROLE_LABELS,
    get_available_roles,
    has_profile,
    resolve_active_role,
)


def _build_role_switch_options(user, active_role):
    """Build role switcher entries for the dashboard header."""
    return [
        {
            'role': role,
            'label': ROLE_LABELS[role],
            'url': reverse('accounts:select_role', args=[role]),
        }
        for role in get_available_roles(user)
        if role != active_role
    ]


def _get_profile_summary_items(user, active_role, user_profile):
    """Return compact account summary items for the Accounts tile."""
    summary_items = [
        {
            'label': 'Usuario',
            'value': user.username,
        },
        {
            'label': 'ID',
            'value': user.national_id,
        },
    ]

    if active_role == 'STUDENT':
        summary_items.append(
            {
                'label': 'Curso',
                'value': f'{user_profile.current_course_type}-{user_profile.current_course_edition}',
            }
        )
    elif active_role == 'INSTRUCTOR':
        summary_items.append(
            {
                'label': 'Funcion',
                'value': user_profile.instructor_type,
            }
        )
    elif active_role == 'STAFF':
        summary_items.append(
            {
                'label': 'Cargo',
                'value': user_profile.position,
            }
        )

    return summary_items


def _build_header_context(user, active_role, user_profile):
    """Build compact header information for the launchpad layout."""
    header_context = {
        'display_name': f'{user.first_name} {user.last_name}'.strip() or user.username,
        'username': user.username,
        'email': user.email,
        'active_role': active_role,
        'active_role_label': ROLE_LABELS.get(active_role, active_role),
        'logout_url': reverse('accounts:logout'),
        'balance': None,
        'show_balance': False,
        'meta_items': [],
    }

    if active_role == 'STUDENT':
        header_context['balance'] = user_profile.balance
        header_context['show_balance'] = True
        header_context['meta_items'] = [
            {
                'label': 'Curso',
                'value': f'{user_profile.current_course_type}-{user_profile.current_course_edition}',
            },
            {
                'label': 'Fase',
                'value': user_profile.student_phase,
            },
        ]
    elif active_role == 'INSTRUCTOR':
        header_context['meta_items'] = [
            {
                'label': 'Función',
                'value': user_profile.instructor_type,
            },
        ]
    elif active_role == 'STAFF':
        header_context['meta_items'] = [
            {
                'label': 'Cargo',
                'value': user_profile.position,
            },
        ]

    return header_context


def _build_launchpad_apps(request, active_role, user_profile):
    """Return only the app cards visible to the current role and permissions."""
    user = request.user
    apps = [
        {
            'key': 'accounts',
            'label': 'Accounts',
            'description': 'Perfil y seguridad de la cuenta.',
            'icon': 'img/user.png',
            'icon_text': 'A',
            'url': reverse('accounts:password_change'),
            'roles': {'STUDENT', 'INSTRUCTOR', 'STAFF'},
            'visible': True,
            'summary_items': _get_profile_summary_items(user, active_role, user_profile),
            'cta_label': 'Cambiar contraseña',
        },
        {
            'key': 'student_sms_report',
            'label': 'Reporte SMS',
            'description': 'Registrar un reporte voluntario.',
            'icon': 'img/shield.png',
            'url': reverse('sms:vhr_form'),
            'roles': {'STUDENT'},
            'visible': True,
        },
        {
            'key': 'student_academics',
            'label': 'Academico',
            'description': 'Consultar el historial académico.',
            'icon': 'img/transcript.png',
            'url': reverse('academic:grade_logs'),
            'roles': {'STUDENT'},
            'visible': True,
        },
        {
            'key': 'student_flightlog',
            'label': 'Bitacora',
            'description': 'Revisar la bitácora personal.',
            'icon': 'img/flightlog.png',
            'url': reverse('fms:student_flightlog'),
            'roles': {'STUDENT'},
            'visible': True,
        },
        {
            'key': 'student_scheduler',
            'label': 'Agenda tu vuelo',
            'description': 'Solicitar y revisar vuelos.',
            'icon': 'img/plane.png',
            'url': reverse('scheduler:student_flight_requests_dashboard'),
            'roles': {'STUDENT'},
            'visible': True,
        },
        {
            'key': 'instructor_academics',
            'label': 'Academico',
            'description': 'Gestionar calificaciones.',
            'icon': 'img/addGrade.png',
            'url': reverse('academic:instructor_grades_dashboard'),
            'roles': {'INSTRUCTOR'},
            'visible': has_profile(user, 'instructor_profile')
            and user.instructor_profile.instructor_type in {'TIERRA', 'DUAL'},
        },
        {
            'key': 'instructor_session_load',
            'label': 'Cargar sesion',
            'description': 'Registrar sesiones de vuelo.',
            'icon': 'img/plane.png',
            'url': reverse('fms:form_selection'),
            'roles': {'INSTRUCTOR'},
            'visible': has_profile(user, 'instructor_profile')
            and user.instructor_profile.instructor_type in {'VUELO', 'DUAL'},
        },
        {
            'key': 'instructor_flightlog',
            'label': 'Bitacora',
            'description': 'Consultar la bitácora de instructor.',
            'icon': 'img/flightlog.png',
            'url': reverse('fms:instructor_flightlog'),
            'roles': {'INSTRUCTOR'},
            'visible': has_profile(user, 'instructor_profile')
            and user.instructor_profile.instructor_type in {'VUELO', 'DUAL'},
        },
        {
            'key': 'instructor_sms_report',
            'label': 'Agregar RVP',
            'description': 'Registrar un reporte voluntario.',
            'icon': 'img/shield.png',
            'url': reverse('sms:vhr_form'),
            'roles': {'INSTRUCTOR'},
            'visible': True,
        },
        {
            'key': 'staff_fms',
            'label': 'FMS',
            'description': 'Acceder al panel de operaciones.',
            'icon': 'img/plane.png',
            'url': reverse('fms:fms_dashboard'),
            'roles': {'STAFF'},
            'visible': True,
        },
        {
            'key': 'staff_sms',
            'label': 'SARA',
            'description': 'Acceder al panel de SMS.',
            'icon': 'img/shield.png',
            'url': reverse('sms:sms_dashboard'),
            'roles': {'STAFF'},
            'visible': user.has_perm('accounts.can_manage_sms'),
        },
        {
            'key': 'staff_transactions',
            'label': 'Transacciones',
            'description': 'Gestionar transacciones y caja.',
            'icon': 'img/money.png',
            'url': reverse('transactions:transactions_dashboard'),
            'roles': {'STAFF'},
            'visible': user.has_perm('accounts.can_manage_transactions'),
        },
        {
            'key': 'staff_scheduler',
            'label': 'Programacion',
            'description': 'Coordinar la programación de vuelos.',
            'icon': 'img/calendar.png',
            'url': reverse('scheduler:staff_flight_requests_dashboard'),
            'roles': {'STAFF'},
            'visible': True,
        },
        {
            'key': 'staff_aura',
            'label': 'AURA',
            'description': 'Acceder al panel de revisión AURA.',
            'icon': 'img/aura.png',
            'url': reverse('aura:staff_aura_dashboard'),
            'roles': {'STAFF'},
            'visible': True,
        },
    ]

    return [
        app for app in apps
        if active_role in app['roles'] and app['visible']
    ]


def _build_dashboard_context(request, active_role, user_profile):
    """Shared dashboard context for the future launchpad implementation."""
    return {
        'launchpad_apps': _build_launchpad_apps(request, active_role, user_profile),
        'dashboard_header': _build_header_context(request.user, active_role, user_profile),
        'role_switch_options': _build_role_switch_options(request.user, active_role),
    }

@login_required
def dashboard(request):
    """
    Display the appropriate dashboard based on user role or selected role.
    """

    user = request.user
    
    # Use the most recent valid role from the session or fall back to the default priority.
    selected_role = request.session.get('selected_role')
    active_role = resolve_active_role(user, selected_role)
    
    context = {
        'user': user,
        'active_role': active_role,
        'can_manage_transactions': request.user.has_perm('accounts.can_manage_transactions'),
        'can_manage_sms': request.user.has_perm('accounts.can_manage_sms'),
    }

    try:
        if active_role == 'STUDENT':
            if not hasattr(user, 'student_profile') or not user.student_profile:
                messages.error(request, 'Perfil de estudiante no encontrado.')
                return redirect('accounts:login')
            context['user_profile'] = user.student_profile
            context.update(_build_dashboard_context(request, active_role, user.student_profile))
            template = 'dashboard/launchpad.html'
        elif active_role == 'INSTRUCTOR':
            if not hasattr(user, 'instructor_profile') or not user.instructor_profile:
                messages.error(request, 'Perfil de instructor no encontrado.')
                return redirect('accounts:login')
            context['user_profile'] = user.instructor_profile
            context.update(_build_dashboard_context(request, active_role, user.instructor_profile))
            template = 'dashboard/launchpad.html'
        elif active_role == 'STAFF':
            if not hasattr(user, 'staff_profile') or not user.staff_profile:
                messages.error(request, 'Perfil de staff no encontrado.')
                return redirect('accounts:login')
            context['user_profile'] = user.staff_profile
            context.update(_build_dashboard_context(request, active_role, user.staff_profile))
            template = 'dashboard/launchpad.html'
        else:
            messages.error(request, 'Rol de usuario inválido.')
            return redirect('accounts:login')
            
        return render(request, template, context)
    
    except Exception as e:
        messages.error(request, f'Error al acceder al perfil: {str(e)}')
        return redirect('accounts:login')