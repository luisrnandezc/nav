from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.contrib.staticfiles.finders import find
from accounts.models import User
from .forms import FlightEvaluation0_100Form, FlightEvaluation100_120Form, FlightEvaluation120_170Form, SimEvaluationForm
import weasyprint

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
                evaluation = form.save()  # Save and get the saved instance
                # Generate PDF immediately and return as download
                return generate_pdf_response(evaluation, request)
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

def generate_pdf_response(evaluation, request):
    """Generate PDF from evaluation data and return as HttpResponse."""
    try:
        # Render the PDF template with evaluation data
        html_string = render_to_string('fms/pdf_0_100.html', {
            'evaluation': evaluation
        })
        
        # Get the base URL for static files
        base_url = request.build_absolute_uri('/')
        
        # Find the CSS file path
        css_path = find('pdf.css')
        if css_path:
            css_url = f'file://{css_path}'
        else:
            # Fallback to relative path if static file not found
            css_url = f'{base_url}static/pdf.css'
        
        # Generate PDF using WeasyPrint with CSS
        html_doc = weasyprint.HTML(string=html_string, base_url=base_url)
        pdf = html_doc.write_pdf(stylesheets=[weasyprint.CSS(filename=css_path)] if css_path else None)
        
        # Create HTTP response with PDF content
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="flight_evaluation_0_100_{evaluation.student_id}_{evaluation.session_number}.pdf"'
        
        return response
        
    except Exception as e:
        # Fallback to dashboard redirect if PDF generation fails
        messages.error(request, f'Error al generar el PDF: {str(e)}')
        return redirect('dashboard:dashboard')