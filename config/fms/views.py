from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from accounts.models import User
from .forms import FlightEvaluation0_100Form, FlightEvaluation100_120Form, FlightEvaluation120_170Form, SimEvaluationForm

@login_required
def form_selection(request):
    """Handle form selection."""
    return render(request, 'fms/form_selection.html')

@login_required
def submit_flight_evaluation_0_100(request):
    """Handle flight evaluation form submission."""
    if request.method == 'POST':
        form = FlightEvaluation0_100Form(request.POST, user=request.user)
        if form.is_valid():
            try:
                form.save()  # This will save both FlightEvaluation and FlightLog
                return redirect('dashboard:dashboard')
            except Exception as e:
                messages.error(request, f'Error al guardar la evaluación: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:  
        form = FlightEvaluation0_100Form(user=request.user)

    return render(request, 'fms/flight_evaluation_0_100.html', {'form': form})

@login_required
def submit_flight_evaluation_100_120(request):
    """Handle flight evaluation form submission."""
    if request.method == 'POST':
        form = FlightEvaluation100_120Form(request.POST, user=request.user)
        if form.is_valid():
            try:
                form.save()  # This will save both FlightEvaluation and FlightLog
                return redirect('dashboard:dashboard')
            except Exception as e:
                messages.error(request, f'Error al guardar la evaluación: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:  
        form = FlightEvaluation100_120Form(user=request.user)

    return render(request, 'fms/flight_evaluation_100_120.html', {'form': form})

@login_required
def submit_flight_evaluation_120_170(request):
    """Handle flight evaluation form submission."""
    if request.method == 'POST':
        form = FlightEvaluation120_170Form(request.POST, user=request.user)
        if form.is_valid():
            try:
                form.save()  # This will save both FlightEvaluation and FlightLog
                return redirect('dashboard:dashboard')
            except Exception as e:
                messages.error(request, f'Error al guardar la evaluación: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:  
        form = FlightEvaluation120_170Form(user=request.user)

    return render(request, 'fms/flight_evaluation_120_170.html', {'form': form})

@login_required
def submit_sim_evaluation(request):
    """Handle simulator evaluation form submission."""
    if request.method == 'POST':
        form = SimEvaluationForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                form.save()  # This will save both FlightEvaluation and FlightLog
                return redirect('dashboard:dashboard')
            except Exception as e:
                messages.error(request, f'Error al guardar la evaluación: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:  
        form = SimEvaluationForm(user=request.user)

    return render(request, 'fms/sim_evaluation.html', {'form': form})

@login_required
@require_http_methods(["GET"])
def get_student_data(request):
    """API endpoint to fetch student data by national ID."""
    student_id = request.GET.get('student_id')
    
    if not student_id:
        return JsonResponse({
            'success': False,
            'error': 'Se requiere el ID del estudiante'
        }, status=400)
    
    try:
        # Try to find the student by national_id
        student = User.objects.get(national_id=student_id, role='STUDENT')
        
        # Get current course type
        current_course_type = student.student_profile.current_course_type
        
        # Check if student is enrolled in a course
        if current_course_type == 'N/A':
            return JsonResponse({
                'success': False,
                'error': 'El estudiante no está inscrito en ningún curso'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'data': {
                'student_first_name': student.first_name,
                'student_last_name': student.last_name,
                'student_license_type': student.student_profile.student_license_type,
                'course_type': current_course_type,
                'flight_hours': student.student_profile.flight_hours,
                'sim_hours': student.student_profile.sim_hours,
            }
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Estudiante no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Ocurrió un error al obtener los datos del estudiante'
        }, status=500)
    
@login_required
def pdf_0_100(request):
    """Handle evaluation form PDF."""
    return render(request, 'fms/pdf_0_100.html')