from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.contrib.staticfiles.finders import find
from accounts.models import User
from .forms import FlightEvaluation0_100Form, FlightEvaluation100_120Form, FlightEvaluation120_170Form, SimEvaluationForm, FlightReportForm
from .models import SimEvaluation, FlightEvaluation0_100, FlightEvaluation100_120, FlightEvaluation120_170, FlightReport
import weasyprint
from pathlib import Path

@login_required
def student_flightlog(request):
    """
    Display the flightlog page with flight and simulator logs for the current student.
    """
    user = request.user
    
    # Get student's national ID
    student_id = user.national_id
    
    # Query flight evaluations for the student
    flight_logs = []
    flight_logs.extend(FlightEvaluation0_100.objects.filter(
        student_id=student_id
    ).order_by('-session_date')[:5])
    flight_logs.extend(FlightEvaluation100_120.objects.filter(
        student_id=student_id
    ).order_by('-session_date')[:5])
    flight_logs.extend(FlightEvaluation120_170.objects.filter(
        student_id=student_id
    ).order_by('-session_date')[:5])

    # Sort by date and take last 10
    flight_logs.sort(key=lambda x: x.session_date, reverse=True)
    flight_logs = flight_logs[:10]
    
    # Fetch simulator logs for the student (last 10)
    simulator_logs = SimEvaluation.objects.filter(
        student_id=student_id
    ).order_by('-session_date')[:10]
    
    context = {
        'flight_logs': flight_logs,
        'simulator_logs': simulator_logs,
        'user': user,
    }
    
    return render(request, 'fms/student_flightlog.html', context)

@login_required
def instructor_flightlog(request):
    """
    Display the flightlog page with flight and simulator logs for the current instructor.
    """
    user = request.user
    
    # Get instructor's national ID
    instructor_id = user.national_id
    
    # Query flight evaluations for the instructor
    flight_logs = []
    flight_logs.extend(FlightEvaluation0_100.objects.filter(
        instructor_id=instructor_id
    ).order_by('-session_date')[:5])
    flight_logs.extend(FlightEvaluation100_120.objects.filter(
        instructor_id=instructor_id
    ).order_by('-session_date')[:5])
    flight_logs.extend(FlightEvaluation120_170.objects.filter(
        instructor_id=instructor_id
    ).order_by('-session_date')[:5])

    # Sort by date and take last 10
    flight_logs.sort(key=lambda x: x.session_date, reverse=True)
    flight_logs = flight_logs[:10]
    
    # Fetch simulator logs for the instructor (last 10)
    simulator_logs = SimEvaluation.objects.filter(
        instructor_id=instructor_id
    ).order_by('-session_date')[:10]
    
    context = {
        'flight_logs': flight_logs,
        'simulator_logs': simulator_logs,
        'user': user,
    }
    
    return render(request, 'fms/instructor_flightlog.html', context)

@login_required
def fms_dashboard(request):
    """FMS Dashboard view showing latest flights and sessions."""
    # Get latest 10 records for each category
    latest_sim_sessions = SimEvaluation.objects.all().order_by('-session_date')[:50]
    latest_flight_0_100 = FlightEvaluation0_100.objects.all().order_by('-session_date')[:50]
    latest_flight_100_120 = FlightEvaluation100_120.objects.all().order_by('-session_date')[:50]
    latest_flight_120_170 = FlightEvaluation120_170.objects.all().order_by('-session_date')[:50]
    latest_flight_reports = FlightReport.objects.all().order_by('-flight_date')[:50]
    
    context = {
        'latest_sim_sessions': latest_sim_sessions,
        'latest_flight_0_100': latest_flight_0_100,
        'latest_flight_100_120': latest_flight_100_120,
        'latest_flight_120_170': latest_flight_120_170,
        'latest_flight_reports': latest_flight_reports,
    }
    
    return render(request, 'fms/fms_dashboard.html', context)

@login_required
def form_selection(request):
    """Handle form selection."""
    return render(request, 'fms/form_selection.html')

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
def submit_flight_report(request):
    """Handle flight report form submission."""
    if request.method == 'POST':
        form = FlightReportForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                form.save()
                return redirect('dashboard:dashboard')
            except Exception as e:
                messages.error(request, f'Error al guardar el reporte: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:  
        form = FlightReportForm(user=request.user)

    return render(request, 'fms/flight_report.html', {'form': form})

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
def student_list(request):
    """Display a list of all students with their information."""
    # Get all students with their profiles
    students = User.objects.filter(role='STUDENT').select_related('student_profile').order_by('first_name', 'last_name')
    
    # Create a list of student data similar to admin list_display
    student_data = []
    for student in students:
        try:
            profile = student.student_profile
            student_info = {
                'username': student.username,
                'student_id': student.national_id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'student_phase': profile.student_phase,
                'course_type': profile.current_course_type,
                'course_edition': profile.current_course_edition,
                'balance': profile.balance,
                'flight_hours': profile.flight_hours,
                'sim_hours': profile.sim_hours,
                'student_license_type': profile.student_license_type,
            }
            student_data.append(student_info)
        except Exception as e:
            # Handle students without profiles
            continue
    
    context = {
        'students': student_data,
        'total_students': len(student_data),
    }
    
    return render(request, 'fms/student_list.html', context)

@login_required
def download_pdf(request, form_type, evaluation_id):
    """Download PDF for a specific evaluation."""
    try:
        evaluation, template_name = get_evaluation_and_template(form_type, evaluation_id)
        
        # Find the static image path (logo)
        raw_logo_path = find('img/evaluation_logo.png')
        if raw_logo_path:
            logo_path = Path(raw_logo_path).as_posix()
            logo_uri = f'file:///{logo_path}'
        else:
            logo_uri = ''

        # Render the PDF template with evaluation data and logo path
        html_string = render_to_string(template_name, {
            'evaluation': evaluation,
            'logo_path': logo_uri
        })
        
        # Get the base URL for static files
        base_url = request.build_absolute_uri()

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