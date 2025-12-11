from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import LoginForm
from django.contrib.auth.views import PasswordChangeView
from .forms import CustomPasswordChangeForm
from django.contrib.auth.password_validation import password_validators_help_texts
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from .models import StudentProfile, InstructorProfile, StaffProfile


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, username=cd['username'], password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    # Check if user has multiple roles (multiple profiles)
                    if has_multiple_roles(user):
                        return redirect('accounts:role_selection')
                    else:
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


def has_multiple_roles(user):
    """Check if user has multiple role profiles."""
    profiles_count = 0
    try:
        if hasattr(user, 'student_profile') and user.student_profile:
            profiles_count += 1
    except:
        pass
    
    try:
        if hasattr(user, 'instructor_profile') and user.instructor_profile:
            profiles_count += 1
    except:
        pass
    
    try:
        if hasattr(user, 'staff_profile') and user.staff_profile:
            profiles_count += 1
    except:
        pass
    
    return profiles_count > 1


@login_required
def role_selection(request):
    """Display role selection panel for users with multiple roles."""
    user = request.user
    
    # Check if user actually has multiple roles
    if not has_multiple_roles(user):
        return redirect('dashboard:dashboard')
    
    available_roles = []
    
    # Check which profiles exist
    try:
        if hasattr(user, 'student_profile') and user.student_profile:
            available_roles.append({
                'role': 'STUDENT',
                'name': 'Estudiante',
                'description': 'Acceder al panel de estudiante'
            })
    except:
        pass
    
    try:
        if hasattr(user, 'instructor_profile') and user.instructor_profile:
            available_roles.append({
                'role': 'INSTRUCTOR', 
                'name': 'Instructor',
                'description': 'Acceder al panel de instructor'
            })
    except:
        pass
    
    try:
        if hasattr(user, 'staff_profile') and user.staff_profile:
            available_roles.append({
                'role': 'STAFF',
                'name': 'Staff',
                'description': 'Acceder al panel de staff'
            })
    except:
        pass
    
    context = {
        'user': user,
        'available_roles': available_roles
    }
    
    return render(request, 'accounts/role_selection.html', context)


@login_required
def select_role(request, role):
    """Handle role selection and redirect to appropriate dashboard."""
    user = request.user
    
    # Validate the selected role
    valid_roles = []
    try:
        if hasattr(user, 'student_profile') and user.student_profile:
            valid_roles.append('STUDENT')
    except:
        pass
    
    try:
        if hasattr(user, 'instructor_profile') and user.instructor_profile:
            valid_roles.append('INSTRUCTOR')
    except:
        pass
    
    try:
        if hasattr(user, 'staff_profile') and user.staff_profile:
            valid_roles.append('STAFF')
    except:
        pass
    
    if role not in valid_roles:
        messages.error(request, 'Rol seleccionado no válido.')
        return redirect('accounts:role_selection')
    
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
    return render(request, 'accounts/logout.html')


class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm