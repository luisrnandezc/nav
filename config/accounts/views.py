from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import LoginForm
from django.contrib.auth.views import PasswordChangeView
from .forms import CustomPasswordChangeForm
from django.contrib.auth.password_validation import password_validators_help_texts
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .role_utils import ROLE_LABELS, get_available_roles, resolve_active_role


def _format_date_or_na(value):
    return value.strftime('%d/%m/%Y') if value else 'N/A'


def _document_expiry_class(exp_date):
    """
    CSS class for document expiry emphasis on the account page.
    - Urgent (red): already expired, or fewer than 15 days until expiration.
    - Soon (yellow): between 15 and 30 days inclusive.
    - Normal: more than 30 days; no date -> no class.
    Red wins when both could apply.
    """
    if not exp_date:
        return ''
    today = timezone.localdate()
    delta = (exp_date - today).days
    if delta < 0 or delta < 15:
        return 'account-expiry--urgent'
    if delta <= 30:
        return 'account-expiry--soon'
    return ''


def _doc_row(label, value, exp_date=None):
    """Build one document row for the template; optional expiry styling from date."""
    return {
        'label': label,
        'value': value,
        'value_class': _document_expiry_class(exp_date) if exp_date else '',
    }


def _build_identity_items(user, active_role, user_profile):
    items = [
        {'label': 'Nombre completo', 'value': f'{user.first_name} {user.last_name}'.strip()},
        {'label': 'Usuario', 'value': user.username},
        {'label': 'Email', 'value': user.email},
        {'label': 'ID', 'value': user.national_id},
        {'label': 'Rol activo', 'value': ROLE_LABELS.get(active_role, active_role)},
    ]

    if active_role == 'STUDENT':
        items.extend([
            {'label': 'Curso', 'value': f'{user_profile.current_course_type}-{user_profile.current_course_edition}'},
            {'label': 'Fase', 'value': user_profile.get_student_phase_display()},
            {'label': 'Tipo de licencia', 'value': user_profile.get_student_license_type_display()},
        ])
    elif active_role == 'INSTRUCTOR':
        items.extend([
            {'label': 'Tipo de instructor', 'value': user_profile.get_instructor_type_display()},
            {'label': 'Tipo de licencia', 'value': user_profile.get_instructor_license_type_display()},
        ])
    elif active_role == 'STAFF':
        items.append({'label': 'Cargo', 'value': user_profile.position})

    return items


def _build_document_items(active_role, user_profile):
    if active_role == 'STUDENT':
        license_value = 'N/A'
        if user_profile.student_phase != user_profile.GROUND:
            if user_profile.student_license_type == user_profile.LICENSE_NA:
                license_value = 'N/A'
            elif user_profile.student_license_type == user_profile.LICENSE_AP:
                license_value = user_profile.get_student_license_type_display()
            else:
                license_value = (
                    f'{user_profile.get_student_license_type_display()}'
                )

        return [
            _doc_row(
                'Certificado médico',
                _format_date_or_na(user_profile.medical_exp_date),
                user_profile.medical_exp_date,
            ),
            _doc_row(
                'Licencia AP',
                _format_date_or_na(user_profile.ap_exp_date),
                user_profile.ap_exp_date,
            ),
            _doc_row(
                'Habilitación (PA28)',
                _format_date_or_na(user_profile.rating_exp_date),
                user_profile.rating_exp_date,
            ),
        ]

    if active_role == 'INSTRUCTOR':
        ivs_license_value = 'N/A'
        if user_profile.ivs_exp_date:
            ivs_license_value = f'{_format_date_or_na(user_profile.ivs_exp_date)}'

        iva_license_value = 'N/A'
        if user_profile.iva_exp_date:
            iva_license_value = f'{_format_date_or_na(user_profile.iva_exp_date)}'

        rating_value = 'N/A'
        if user_profile.rating_exp_date:
            rating_value = f'{_format_date_or_na(user_profile.rating_exp_date)}'

        return [
            _doc_row(
                'Certificado médico',
                _format_date_or_na(user_profile.medical_exp_date),
                user_profile.medical_exp_date,
            ),
            _doc_row(
                'Habilitación IVS (ATD)',
                ivs_license_value,
                user_profile.ivs_exp_date,
            ),
            _doc_row(
                'Habilitación IVA (PA28)',
                iva_license_value,
                user_profile.iva_exp_date,
            ),
            _doc_row(
                'Habilitación (PA28)',
                rating_value,
                user_profile.rating_exp_date,
            ),
        ]

    return []


def _get_active_profile(user, active_role):
    if active_role == 'STUDENT' and hasattr(user, 'student_profile'):
        return user.student_profile
    if active_role == 'INSTRUCTOR' and hasattr(user, 'instructor_profile'):
        return user.instructor_profile
    if active_role == 'STAFF' and hasattr(user, 'staff_profile'):
        return user.staff_profile
    return None


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, username=cd['username'], password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    # A fresh login should always fall back to the default role priority.
                    if 'selected_role' in request.session:
                        del request.session['selected_role']
                    return redirect('dashboard:dashboard')
                else:
                    messages.error(request, 'Cuenta inactiva.')
            else:
                messages.error(request, 'Credenciales inválidas.')
    else:
        # Clear all messages from previous sessions/apps when displaying login page
        # This ensures only login-related messages are shown
        # Iterating through messages marks them as consumed
        list(messages.get_messages(request))
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def account_home(request):
    """Display the account summary for the currently active role."""
    active_role = resolve_active_role(request.user, request.session.get('selected_role'))
    user_profile = _get_active_profile(request.user, active_role)

    if not user_profile:
        messages.error(request, 'No se encontró el perfil asociado al rol activo.')
        return redirect('dashboard:dashboard')

    context = {
        'active_role': active_role,
        'active_role_label': ROLE_LABELS.get(active_role, active_role),
        'identity_items': _build_identity_items(request.user, active_role, user_profile),
        'document_items': _build_document_items(active_role, user_profile),
        'password_change_url': reverse('accounts:password_change'),
        'dashboard_url': reverse('dashboard:dashboard'),
    }
    return render(request, 'accounts/account_home.html', context)


@login_required
def select_role(request, role):
    """Handle role selection and redirect to appropriate dashboard."""
    user = request.user

    valid_roles = get_available_roles(user)

    if role not in valid_roles:
        messages.error(request, 'Rol seleccionado no válido.')
        return redirect('dashboard:dashboard')
    
    # Store selected role in session
    request.session['selected_role'] = role
    
    # Redirect to dashboard
    return redirect('dashboard:dashboard')


def user_logout(request):
    # Clear the selected role from session
    if 'selected_role' in request.session:
        del request.session['selected_role']
    
    # Clear all messages before logout to prevent them from appearing on login page
    # Iterating through messages marks them as consumed
    list(messages.get_messages(request))
    
    logout(request)
    return redirect('accounts:login')


class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm