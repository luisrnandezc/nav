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