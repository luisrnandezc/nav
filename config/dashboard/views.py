from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import StudentProfile, InstructorProfile, StaffProfile
from django.contrib import messages

@login_required
def dashboard(request):
    """
    Display the appropriate dashboard based on user role or selected role.
    """

    user = request.user
    
    # Check if user has a selected role in session (for dual-role users)
    selected_role = request.session.get('selected_role')
    
    # Determine which role to use
    if selected_role:
        # Use the selected role from session
        active_role = selected_role
    else:
        # Use the user's primary role
        active_role = user.role
    
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
            template = 'dashboard/student_dashboard.html'
        elif active_role == 'INSTRUCTOR':
            if not hasattr(user, 'instructor_profile') or not user.instructor_profile:
                messages.error(request, 'Perfil de instructor no encontrado.')
                return redirect('accounts:login')
            context['user_profile'] = user.instructor_profile
            template = 'dashboard/instructor_dashboard.html'
        elif active_role == 'STAFF':
            if not hasattr(user, 'staff_profile') or not user.staff_profile:
                messages.error(request, 'Perfil de staff no encontrado.')
                return redirect('accounts:login')
            context['user_profile'] = user.staff_profile
            template = 'dashboard/staff_dashboard.html'
        else:
            messages.error(request, 'Rol de usuario inválido.')
            return redirect('accounts:login')
            
        return render(request, template, context)
    
    except Exception as e:
        messages.error(request, f'Error al acceder al perfil: {str(e)}')
        return redirect('accounts:login')