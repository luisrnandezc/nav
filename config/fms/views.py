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
                # Redirect to intermediate download page
                return redirect('fms:pdf_download_waiting_page', form_type='0_100', evaluation_id=evaluation.id)
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
                evaluation = form.save()  # Save and get the saved instance
                # Redirect to intermediate download page
                return redirect('fms:pdf_download_waiting_page', form_type='100_120', evaluation_id=evaluation.id)
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
                evaluation = form.save()  # Save and get the saved instance
                # Redirect to intermediate download page
                return redirect('fms:pdf_download_waiting_page', form_type='120_170', evaluation_id=evaluation.id)
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
                evaluation = form.save()  # Save and get the saved instance
                # Redirect to intermediate download page
                return redirect('fms:pdf_download_waiting_page', form_type='sim', evaluation_id=evaluation.id)
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

def get_evaluation_and_template(form_type, evaluation_id):
    """Helper function to get evaluation and template based on form_type."""
    if form_type == '0_100':
        from .models import FlightEvaluation0_100
        evaluation = FlightEvaluation0_100.objects.get(id=evaluation_id)
        template_name = 'fms/pdf_0_100.html'
    elif form_type == '100_120':
        from .models import FlightEvaluation100_120
        evaluation = FlightEvaluation100_120.objects.get(id=evaluation_id)
        template_name = 'fms/pdf_100_120.html'
    elif form_type == '120_170':
        from .models import FlightEvaluation120_170
        evaluation = FlightEvaluation120_170.objects.get(id=evaluation_id)
        template_name = 'fms/pdf_120_170.html'
    elif form_type == 'sim':
        from .models import SimEvaluation
        evaluation = SimEvaluation.objects.get(id=evaluation_id)
        template_name = 'fms/pdf_sim.html'
    else:
        raise ValueError(f'Invalid form_type: {form_type}')
    
    return evaluation, template_name

@login_required
def pdf_download_waiting_page(request, form_type, evaluation_id):
    """Show intermediate page for PDF download."""
    try:
        evaluation, _ = get_evaluation_and_template(form_type, evaluation_id)
        
        context = {
            'pdf_url': f'/fms/download_pdf/{form_type}/{evaluation_id}/',
            'filename': f'flight_evaluation_{form_type}_{evaluation.student_id}_{evaluation.session_number}.pdf',
            'dashboard_url': '/dashboard/'
        }
        
        return render(request, 'fms/pdf_download.html', context)
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('dashboard:dashboard')

@login_required
def download_pdf(request, form_type, evaluation_id):
    """Download PDF for a specific evaluation."""
    try:
        evaluation, template_name = get_evaluation_and_template(form_type, evaluation_id)
        
        # Render the PDF template with evaluation data
        html_string = render_to_string(template_name, {
            'evaluation': evaluation
        })
        
        # Get the base URL for static files
        base_url = request.build_absolute_uri('/')
        
        # Find the CSS file path
        css_path = find('pdf.css')
        
        # Generate PDF using WeasyPrint with CSS
        html_doc = weasyprint.HTML(string=html_string, base_url=base_url)
        pdf = html_doc.write_pdf(stylesheets=[weasyprint.CSS(filename=css_path)] if css_path else None)
        
        # Create HTTP response with PDF content
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="flight_evaluation_{form_type}_{evaluation.student_id}_{evaluation.session_number}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error al generar el PDF: {str(e)}')
        return redirect('dashboard:dashboard')