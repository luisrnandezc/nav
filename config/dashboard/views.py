from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import StudentProfile, InstructorProfile, StaffProfile
from django.contrib import messages

@login_required
def dashboard(request):
    """
    Display the appropriate dashboard based on user role.
    """
    user = request.user
    context = {'user': user}

    try:
        if user.role == 'STUDENT':
            context['user_profile'] = user.student_profile
            template = 'dashboard/student_dashboard.html'
        elif user.role == 'INSTRUCTOR':
            context['user_profile'] = user.instructor_profile
            template = 'dashboard/instructor_dashboard.html'
        elif user.role == 'STAFF':
            context['user_profile'] = user.staff_profile
            template = 'dashboard/staff_dashboard.html'
        else:
            messages.error(request, 'Perfil de usuario inválido.')
            return redirect('accounts:login')
            
        return render(request, template, context)
    
    except (StudentProfile.DoesNotExist, InstructorProfile.DoesNotExist, StaffProfile.DoesNotExist):
        messages.error(request, 'No se encontró el perfil de usuario.')
        return redirect('accounts:login')