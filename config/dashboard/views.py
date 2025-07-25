from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import StudentProfile, InstructorProfile
from fms.models import FlightLog, SimulatorLog
from django.contrib import messages
from academic.models import StudentGrade

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
        else:
            messages.error(request, 'Perfil de usuario inválido.')
            return redirect('accounts:login')
            
        return render(request, template, context)
    
    except (StudentProfile.DoesNotExist, InstructorProfile.DoesNotExist):
        messages.error(request, 'No se encontró el perfil de usuario.')
        return redirect('accounts:login')

@login_required
def student_logs(request):
    """
    Display the logs page with flight and simulator logs for the current student.
    """
    user = request.user
    
    # Get student's national ID
    student_id = user.national_id
    
    # Fetch flight logs for the student (last 10)
    flight_logs = FlightLog.objects.filter(
        student_id=student_id
    ).order_by('-session_date')[:10]
    
    # Fetch simulator logs for the student (last 10)
    simulator_logs = SimulatorLog.objects.filter(
        student_id=student_id
    ).order_by('-session_date')[:10]
    
    context = {
        'flight_logs': flight_logs,
        'simulator_logs': simulator_logs,
        'user': user,
    }
    
    return render(request, 'dashboard/student_log.html', context)

@login_required
def instructor_logs(request):
    """
    Display the logs page with flight and simulator logs for the current instructor.
    """
    user = request.user
    
    # Get instructor's national ID
    instructor_id = user.national_id
    
    # Fetch flight logs for the instructor (last 10)
    flight_logs = FlightLog.objects.filter(
        instructor_id=instructor_id
    ).order_by('-session_date')[:10]
    
    # Fetch simulator logs for the instructor (last 10)
    simulator_logs = SimulatorLog.objects.filter(
        instructor_id=instructor_id
    ).order_by('-session_date')[:10]
    
    context = {
        'flight_logs': flight_logs,
        'simulator_logs': simulator_logs,
        'user': user,
    }
    
    return render(request, 'dashboard/instructor_log.html', context)

@login_required
def grade_logs(request):
    """
    Display the grade logs page for the current student.
    """
    user = request.user
    
    # Fetch grade logs for the student (last 10)
    grade_logs = StudentGrade.objects.filter(
        student=user
    ).order_by('-date')[:10]
    
    context = {
        'grade_logs': grade_logs,
        'user': user,
    }
    
    return render(request, 'dashboard/grade_log.html', context)