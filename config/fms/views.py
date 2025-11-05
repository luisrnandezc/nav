from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.contrib.staticfiles.finders import find
from django.contrib.auth.models import Group
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
    
    # Query flight evaluations for the student, separated by evaluation type
    latest_flight_0_100 = FlightEvaluation0_100.objects.filter(
        student_id=student_id
    ).order_by('-session_date')
    
    latest_flight_100_120 = FlightEvaluation100_120.objects.filter(
        student_id=student_id
    ).order_by('-session_date')
    
    latest_flight_120_170 = FlightEvaluation120_170.objects.filter(
        student_id=student_id
    ).order_by('-session_date')
    
    # Fetch simulator logs for the student
    latest_sim_sessions = SimEvaluation.objects.filter(
        student_id=student_id
    ).order_by('-session_date')
    
    context = {
        'latest_flight_0_100': latest_flight_0_100,
        'latest_flight_100_120': latest_flight_100_120,
        'latest_flight_120_170': latest_flight_120_170,
        'latest_sim_sessions': latest_sim_sessions,
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
    
    # Query flight evaluations for the instructor, separated by evaluation type
    latest_flight_0_100 = FlightEvaluation0_100.objects.filter(
        instructor_id=instructor_id
    ).order_by('-session_date')
    
    latest_flight_100_120 = FlightEvaluation100_120.objects.filter(
        instructor_id=instructor_id
    ).order_by('-session_date')
    
    latest_flight_120_170 = FlightEvaluation120_170.objects.filter(
        instructor_id=instructor_id
    ).order_by('-session_date')
    
    # Fetch simulator logs for the instructor
    latest_sim_sessions = SimEvaluation.objects.filter(
        instructor_id=instructor_id
    ).order_by('-session_date')
    
    context = {
        'latest_flight_0_100': latest_flight_0_100,
        'latest_flight_100_120': latest_flight_100_120,
        'latest_flight_120_170': latest_flight_120_170,
        'latest_sim_sessions': latest_sim_sessions,
        'user': user,
    }
    
    return render(request, 'fms/instructor_flightlog.html', context)

@login_required
@require_http_methods(["GET"])
def load_more_flights(request):
    """
    AJAX endpoint to load more flight logs for instructor flightlog page.
    """
    user = request.user
    instructor_id = user.national_id
    
    # Get offset from request
    offset = int(request.GET.get('offset', 0))
    limit = int(request.GET.get('limit', 30))  # Load 30 flights per request
    
    # Get all flight evaluations for the instructor and sort by date
    all_flight_logs = []
    all_flight_logs.extend(FlightEvaluation0_100.objects.filter(
        instructor_id=instructor_id
    ))
    all_flight_logs.extend(FlightEvaluation100_120.objects.filter(
        instructor_id=instructor_id
    ))
    all_flight_logs.extend(FlightEvaluation120_170.objects.filter(
        instructor_id=instructor_id
    ))

    # Sort by date (newest first)
    all_flight_logs.sort(key=lambda x: x.session_date, reverse=True)
    
    # Apply pagination
    flight_logs = all_flight_logs[offset:offset+limit]
    
    # Check if there are more flights available
    total_flights = len(all_flight_logs)
    has_more = (offset + len(flight_logs)) < total_flights
    
    # Render the flight rows HTML
    flight_rows_html = render_to_string('fms/partials/flight_log_rows.html', {
        'flight_logs': flight_logs
    })
    
    return JsonResponse({
        'html': flight_rows_html,
        'has_more': has_more,
        'loaded_count': len(flight_logs),
        'total_count': total_flights
    })

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
    
    # Check if user is in director group
    is_director = request.user.groups.filter(name='director').exists()
    
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
                'nav_flight_hours': profile.nav_flight_hours,
                'sim_hours': profile.sim_hours,
                'student_license_type': profile.student_license_type,
                'has_temp_permission': profile.has_temp_permission,
            }
            student_data.append(student_info)
        except Exception as e:
            # Handle students without profiles
            continue
    
    context = {
        'students': student_data,
        'total_students': len(student_data),
        'is_director': is_director,
    }
    
    return render(request, 'fms/student_list.html', context)

@login_required
@require_http_methods(["POST"])
def toggle_temp_permission(request):
    """Toggle has_temp_permission for a student. Only accessible by directors."""
    # Check if user is in director group
    if not request.user.groups.filter(name='director').exists():
        return JsonResponse({
            'success': False,
            'error': 'No tienes permisos para realizar esta acción'
        }, status=403)
    
    student_id = request.POST.get('student_id')
    if not student_id:
        return JsonResponse({
            'success': False,
            'error': 'Se requiere el ID del estudiante'
        }, status=400)
    
    try:
        # Find the student by national_id
        student = User.objects.get(national_id=student_id, role='STUDENT')
        profile = student.student_profile
        
        # Toggle the has_temp_permission field
        profile.has_temp_permission = not profile.has_temp_permission
        profile.save()
        
        return JsonResponse({
            'success': True,
            'has_temp_permission': profile.has_temp_permission,
            'message': f'Permiso temporal {"activado" if profile.has_temp_permission else "desactivado"} para {student.first_name} {student.last_name}'
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Estudiante no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al actualizar el permiso: {str(e)}'
        }, status=500)

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

def get_evaluation_fields(form_type):
    """Get field labels organized by category for each evaluation type."""
    from .forms import FlightEvaluation0_100Form, FlightEvaluation100_120Form, FlightEvaluation120_170Form, SimEvaluationForm
    
    form = None
    if form_type == '0_100':
        form = FlightEvaluation0_100Form()
        categories = {
            'Pre-vuelo/encendido/taxeo': ['pre_1', 'pre_2', 'pre_3', 'pre_4', 'pre_5', 'pre_6'],
            'Despegue/salida visual': ['to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6'],
            'Maniobras básicas/avanzadas': ['mvrs_1', 'mvrs_2', 'mvrs_3', 'mvrs_4', 'mvrs_5', 'mvrs_6', 'mvrs_7', 'mvrs_8', 'mvrs_9', 'mvrs_10', 'mvrs_11', 'mvrs_12', 'mvrs_13', 'mvrs_14', 'mvrs_15', 'mvrs_16', 'mvrs_17', 'mvrs_18'],
            'Navegación VFR': ['nav_1', 'nav_2', 'nav_3', 'nav_4', 'nav_5', 'nav_6'],
            'Circuito/procedimiento': ['land_1', 'land_2', 'land_3', 'land_4', 'land_5', 'land_6', 'land_7', 'land_8', 'land_9', 'land_10'],
            'Emergencias': ['emer_1', 'emer_2', 'emer_3', 'emer_4', 'emer_5', 'emer_6'],
            'Evaluación general': ['gen_1', 'gen_2', 'gen_3', 'gen_4', 'gen_5', 'gen_6', 'gen_7'],
        }
    elif form_type == '100_120':
        form = FlightEvaluation100_120Form()
        categories = {
            'Pre-vuelo/encendido/taxeo': ['pre_1', 'pre_2', 'pre_3', 'pre_4', 'pre_5', 'pre_6'],
            'Despegue/salida instrumental': ['to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6'],
            'Maniobras IFR básicas': ['b_ifr_1', 'b_ifr_2', 'b_ifr_3', 'b_ifr_4', 'b_ifr_5', 'b_ifr_6', 'b_ifr_7', 'b_ifr_8', 'b_ifr_9', 'b_ifr_10', 'b_ifr_11'],
            'Procedimientos IFR avanzados': ['a_ifr_1', 'a_ifr_2', 'a_ifr_3', 'a_ifr_4', 'a_ifr_5', 'a_ifr_6', 'a_ifr_7', 'a_ifr_8', 'a_ifr_9', 'a_ifr_10', 'a_ifr_11'],
            'Aproximación final y aterrizaje': ['land_1', 'land_2', 'land_3', 'land_4', 'land_5', 'land_6', 'land_7'],
            'Emergencias': ['emer_1', 'emer_2', 'emer_3', 'emer_4', 'emer_5'],
            'Evaluación general': ['gen_1', 'gen_2', 'gen_3', 'gen_4', 'gen_5', 'gen_6', 'gen_7'],
        }
    elif form_type == '120_170':
        form = FlightEvaluation120_170Form()
        categories = {
            'Pre-vuelo/encendido/taxeo': ['pre_1', 'pre_2', 'pre_3', 'pre_4', 'pre_5', 'pre_6'],
            'Despegue/Salida VFR/IFR': ['to_1', 'to_2', 'to_3', 'to_4', 'to_5', 'to_6'],
            'Instrumentos avanzados': ['inst_1', 'inst_2', 'inst_3', 'inst_4', 'inst_5', 'inst_6', 'inst_7', 'inst_8', 'inst_9', 'inst_10', 'inst_11'],
            'Aproximación final y aterrizaje': ['land_1', 'land_2', 'land_3', 'land_4', 'land_5', 'land_6', 'land_7'],
            'Emergencias situacionales (simuladas)': ['emer_1', 'emer_2', 'emer_3', 'emer_4'],
            'Evaluación general': ['gen_1', 'gen_2', 'gen_3', 'gen_4', 'gen_5', 'gen_6', 'gen_7'],
        }
    elif form_type == 'sim':
        form = SimEvaluationForm()
        # Get categories from sim form - need to check the form structure
        categories = {
            'Pre-vuelo': ['pre_1', 'pre_2', 'pre_3'],
            'Despegue': ['to_1', 'to_2', 'to_3', 'to_4', 'to_5'],
            'Procedimiento de salida': ['dep_1', 'dep_2', 'dep_3', 'dep_4', 'dep_5'],
            'Instrumentos básicos': ['inst_1', 'inst_2', 'inst_3', 'inst_4', 'inst_5', 'inst_6', 'inst_7', 'inst_8', 'inst_9', 'inst_10', 'inst_11', 'inst_12', 'inst_13'],
            'Actitudes anormales': ['upset_1', 'upset_2', 'upset_3'],
            'Misceláneos': ['misc_1', 'misc_2', 'misc_3', 'misc_4', 'misc_5', 'misc_6', 'misc_7'],
            'Uso de radioayudas (VOR)': ['radio_1', 'radio_2', 'radio_3', 'radio_4', 'radio_5', 'radio_6', 'radio_7', 'radio_8', 'radio_9', 'radio_10', 'radio_11'],
            'Uso de radioayudas (ADF)': ['radio_12', 'radio_13', 'radio_14', 'radio_15', 'radio_16', 'radio_17', 'radio_18', 'radio_19', 'radio_20', 'radio_21', 'radio_22'],
            'Aproximaciones (ILS)': ['app_1', 'app_2', 'app_3', 'app_4', 'app_5', 'app_6', 'app_7', 'app_8'],
            'Aproximaciones (VOR)': ['app_9', 'app_10', 'app_11', 'app_12', 'app_13', 'app_14', 'app_15', 'app_16'],
            'Aproximaciones (ADF)': ['app_17', 'app_18', 'app_19', 'app_20', 'app_21', 'app_22', 'app_23', 'app_24'],
            'Go-around': ['go_1', 'go_2'],
        }
    else:
        form = None
        categories = {}
    
    # Build field data with labels and values
    field_data = {}
    for category, field_names in categories.items():
        field_data[category] = []
        for field_name in field_names:
            if form and hasattr(form, 'fields') and field_name in form.fields:
                label = form.fields[field_name].label or field_name
                field_data[category].append({
                    'name': field_name,
                    'label': label
                })
    
    return field_data

@login_required
def session_detail(request, form_type, evaluation_id):
    """Display detailed view of a flight or simulator session."""
    try:
        evaluation, _ = get_evaluation_and_template(form_type, evaluation_id)
        
        # Determine the return URL based on selected role in session, fallback to user role
        selected_role = request.session.get('selected_role', None)
        user_role = selected_role if selected_role else request.user.role
        
        if user_role == 'STUDENT':
            return_url = 'fms:student_flightlog'
        elif user_role == 'INSTRUCTOR':
            return_url = 'fms:instructor_flightlog'
        elif user_role == 'STAFF':
            return_url = 'fms:fms_dashboard'
        
        # Get organized field data
        field_data = get_evaluation_fields(form_type)
        
        # Add field values and split into two columns for each category
        for category, fields in field_data.items():
            for field in fields:
                field_value = getattr(evaluation, field['name'], None)
                field['value'] = field_value
            
            # Split fields into two columns
            total_fields = len(fields)
            if total_fields > 0:
                mid_point = (total_fields + 1) // 2  # Split as evenly as possible
                field_data[category] = {
                    'left': fields[:mid_point],
                    'right': fields[mid_point:]
                }
        
        context = {
            'evaluation': evaluation,
            'form_type': form_type,
            'return_url': return_url,
            'field_data': field_data,
        }
        
        return render(request, 'fms/session_detail.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar la sesión: {str(e)}')
        return redirect('dashboard:dashboard')