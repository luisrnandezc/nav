from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.contrib.staticfiles.finders import find
from django.contrib.auth.models import Group
from django.db.models import Sum
from decimal import Decimal
from accounts.models import User, StudentProfile, InstructorProfile
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
    ).order_by('-session_date')[:10]
    
    latest_flight_100_120 = FlightEvaluation100_120.objects.filter(
        student_id=student_id
    ).order_by('-session_date')[:10]
    
    latest_flight_120_170 = FlightEvaluation120_170.objects.filter(
        student_id=student_id
    ).order_by('-session_date')[:10]
    
    # Fetch simulator logs for the student
    latest_sim_sessions = SimEvaluation.objects.filter(
        student_id=student_id
    ).order_by('-session_date')[:10]
    
    # Determine user role from session or user
    selected_role = request.session.get('selected_role', None)
    user_role = 'student' if selected_role == 'STUDENT' else (selected_role or 'student').lower()
    
    context = {
        'latest_flight_0_100': latest_flight_0_100,
        'latest_flight_100_120': latest_flight_100_120,
        'latest_flight_120_170': latest_flight_120_170,
        'latest_sim_sessions': latest_sim_sessions,
        'user': user,
        'user_role': user_role,
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
    ).order_by('-session_date')[:10]
    
    latest_flight_100_120 = FlightEvaluation100_120.objects.filter(
        instructor_id=instructor_id
    ).order_by('-session_date')[:10]
    
    latest_flight_120_170 = FlightEvaluation120_170.objects.filter(
        instructor_id=instructor_id
    ).order_by('-session_date')[:10]
    
    # Fetch simulator logs for the instructor
    latest_sim_sessions = SimEvaluation.objects.filter(
        instructor_id=instructor_id
    ).order_by('-session_date')[:10]
    
    # Determine user role from session or user
    selected_role = request.session.get('selected_role', None)
    user_role = 'instructor' if selected_role == 'INSTRUCTOR' else (selected_role or 'instructor').lower()
    
    context = {
        'latest_flight_0_100': latest_flight_0_100,
        'latest_flight_100_120': latest_flight_100_120,
        'latest_flight_120_170': latest_flight_120_170,
        'latest_sim_sessions': latest_sim_sessions,
        'user': user,
        'user_role': user_role,
    }
    
    return render(request, 'fms/instructor_flightlog.html', context)

@login_required
@require_http_methods(["GET"])
def load_more_flights(request):
    """
    AJAX endpoint to load more flight logs for flightlog pages.
    Supports different evaluation types and user roles.
    """
    user = request.user
    user_id = user.national_id
    
    # Get parameters from request
    evaluation_type = request.GET.get('type')  # '0_100', '100_120', '120_170', 'sim'
    user_role = request.GET.get('role')  # 'student', 'instructor', 'staff'
    offset = int(request.GET.get('offset', 0))
    limit = int(request.GET.get('limit', 20))
    
    # Get the queryset based on evaluation type and user role
    if evaluation_type == '0_100':
        if user_role == 'student':
            queryset = FlightEvaluation0_100.objects.filter(student_id=user_id).order_by('-session_date')
        elif user_role == 'instructor':
            queryset = FlightEvaluation0_100.objects.filter(instructor_id=user_id).order_by('-session_date')
        else:  # staff - show all
            queryset = FlightEvaluation0_100.objects.all().order_by('-session_date')
        template_name = 'fms/partials/flight_card_0_100.html'
    elif evaluation_type == '100_120':
        if user_role == 'student':
            queryset = FlightEvaluation100_120.objects.filter(student_id=user_id).order_by('-session_date')
        elif user_role == 'instructor':
            queryset = FlightEvaluation100_120.objects.filter(instructor_id=user_id).order_by('-session_date')
        else:  # staff - show all
            queryset = FlightEvaluation100_120.objects.all().order_by('-session_date')
        template_name = 'fms/partials/flight_card_100_120.html'
    elif evaluation_type == '120_170':
        if user_role == 'student':
            queryset = FlightEvaluation120_170.objects.filter(student_id=user_id).order_by('-session_date')
        elif user_role == 'instructor':
            queryset = FlightEvaluation120_170.objects.filter(instructor_id=user_id).order_by('-session_date')
        else:  # staff - show all
            queryset = FlightEvaluation120_170.objects.all().order_by('-session_date')
        template_name = 'fms/partials/flight_card_120_170.html'
    elif evaluation_type == 'sim':
        if user_role == 'student':
            queryset = SimEvaluation.objects.filter(student_id=user_id).order_by('-session_date')
        elif user_role == 'instructor':
            queryset = SimEvaluation.objects.filter(instructor_id=user_id).order_by('-session_date')
        else:  # staff - show all
            queryset = SimEvaluation.objects.all().order_by('-session_date')
        template_name = 'fms/partials/flight_card_sim.html'
    else:
        return JsonResponse({'error': 'Invalid evaluation type'}, status=400)
    
    # Get total count before pagination
    total_count = queryset.count()
    
    # Apply pagination
    sessions = list(queryset[offset:offset+limit])
    
    # Check if there are more flights available
    # has_more should be true if there are records beyond what we've fetched
    if limit == 1:
        # When checking (limit=1), if offset < total_count, there are records at that offset to show
        has_more = offset < total_count
    else:
        # When loading (limit=20), check if there are more beyond what we fetched
        has_more = (offset + len(sessions)) < total_count
    
    # Render the flight cards HTML
    flight_cards_html = render_to_string(template_name, {
        'sessions': sessions,
        'user_role': user_role,
    })
    
    return JsonResponse({
        'html': flight_cards_html,
        'has_more': has_more,
        'loaded_count': len(sessions),
        'total_count': total_count
    })

@login_required
def fms_dashboard(request):
    """FMS Dashboard view showing latest flights and sessions."""
    # Get latest 10 records for each category
    latest_sim_sessions = SimEvaluation.objects.all().order_by('-session_date')[:10]
    latest_flight_0_100 = FlightEvaluation0_100.objects.all().order_by('-session_date')[:10]
    latest_flight_100_120 = FlightEvaluation100_120.objects.all().order_by('-session_date')[:10]
    latest_flight_120_170 = FlightEvaluation120_170.objects.all().order_by('-session_date')[:10]
    latest_flight_reports = FlightReport.objects.all().order_by('-flight_date')[:10]
    
    # Determine user role from session or user
    selected_role = request.session.get('selected_role', None)
    user_role = 'staff' if selected_role == 'STAFF' else (selected_role or 'staff').lower()
    
    context = {
        'latest_sim_sessions': latest_sim_sessions,
        'latest_flight_0_100': latest_flight_0_100,
        'latest_flight_100_120': latest_flight_100_120,
        'latest_flight_120_170': latest_flight_120_170,
        'latest_flight_reports': latest_flight_reports,
        'user_role': user_role,
    }
    
    return render(request, 'fms/fms_dashboard.html', context)

@login_required
def form_selection(request):
    """Handle form selection."""

    selected_role = request.session.get('selected_role', None)
    user_role = selected_role if selected_role else request.user.role

    context = {
        'user_role': user_role
    }

    return render(request, 'fms/form_selection.html', context)

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

    selected_role = request.session.get('selected_role', None)
    user_role = selected_role if selected_role else request.user.role

    context = {
        'form': form,
        'user_role': user_role
    }

    return render(request, 'fms/flight_report.html', context)

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

def calculate_user_stats(user_id, role_type='student', instructor_hourly_rate=None, student_hourly_rate=None):
    """
    Helper function to calculate statistics for a user (student or instructor).
    
    Args:
        user_id: The national_id of the user
        role_type: Either 'student' or 'instructor' to determine which field to filter by
        instructor_hourly_rate: The hourly rate of the instructor
        student_hourly_rate: The hourly rate of the student
    Returns:
        Dictionary with all calculated statistics.
    
    Raises:
        Aircraft.DoesNotExist if aircraft are not found.
    """
    from fleet.models import Aircraft
    
    # Get aircraft data
    yv204e = Aircraft.objects.get(registration='YV204E')
    yv206e = Aircraft.objects.get(registration='YV206E')
    hourly_rate_yv204e = yv204e.hourly_rate
    hourly_rate_yv206e = yv206e.hourly_rate
    fuel_cost_yv204e = yv204e.fuel_cost
    fuel_cost_yv206e = yv206e.fuel_cost

    if role_type == 'student' and student_hourly_rate is not None:
        hourly_rate_yv204e = student_hourly_rate
        hourly_rate_yv206e = student_hourly_rate

    # Determine which field to filter by based on role
    filter_field = 'student_id' if role_type == 'student' else 'instructor_id'

    # Initialize totals
    total_flight_hours = Decimal('0.0')
    total_flight_hours_yv204e = Decimal('0.0')
    total_flight_hours_yv206e = Decimal('0.0')
    total_consumed_liters_yv204e = Decimal('0.0')
    total_consumed_liters_yv206e = Decimal('0.0')
    total_consumed_gallons_yv204e = Decimal('0.0')
    total_consumed_gallons_yv206e = Decimal('0.0')
    fuel_rate_liters_yv204e = Decimal('0.0')
    fuel_rate_liters_yv206e = Decimal('0.0')
    fuel_rate_gallons_yv204e = Decimal('0.0')
    fuel_rate_gallons_yv206e = Decimal('0.0')
    flight_hour_cost_yv204e = Decimal('0.0')
    flight_hour_cost_yv206e = Decimal('0.0')
    total_paid_to_instructor_yv204e = Decimal('0.0')
    total_paid_to_instructor_yv206e = Decimal('0.0')
    total_paid_to_instructor = Decimal('0.0')
    
    # Build filter kwargs dynamically
    filter_kwargs_yv204e = {filter_field: user_id, 'aircraft__registration': 'YV204E'}
    filter_kwargs_yv206e = {filter_field: user_id, 'aircraft__registration': 'YV206E'}
    
    # Sum flight hours and fuel from all three evaluation types
    flight_0_100_stats_yv204e = FlightEvaluation0_100.objects.filter(
        **filter_kwargs_yv204e
    ).aggregate(
        total_hours=Sum('session_flight_hours'),
        total_fuel=Sum('fuel_consumed')
    )
    flight_0_100_stats_yv206e = FlightEvaluation0_100.objects.filter(
        **filter_kwargs_yv206e
    ).aggregate(
        total_hours=Sum('session_flight_hours'),
        total_fuel=Sum('fuel_consumed')
    )

    flight_100_120_stats_yv204e = FlightEvaluation100_120.objects.filter(
        **filter_kwargs_yv204e
    ).aggregate(
        total_hours=Sum('session_flight_hours'),
        total_fuel=Sum('fuel_consumed')
    )
    flight_100_120_stats_yv206e = FlightEvaluation100_120.objects.filter(
        **filter_kwargs_yv206e
    ).aggregate(
        total_hours=Sum('session_flight_hours'),
        total_fuel=Sum('fuel_consumed')
    )
    
    flight_120_170_stats_yv204e = FlightEvaluation120_170.objects.filter(
        **filter_kwargs_yv204e
    ).aggregate(
        total_hours=Sum('session_flight_hours'),
        total_fuel=Sum('fuel_consumed')
    )
    flight_120_170_stats_yv206e = FlightEvaluation120_170.objects.filter(
        **filter_kwargs_yv206e
    ).aggregate(
        total_hours=Sum('session_flight_hours'),
        total_fuel=Sum('fuel_consumed')
    )
    
    # Add up all the totals
    if flight_0_100_stats_yv204e['total_hours']:
        total_flight_hours_yv204e += flight_0_100_stats_yv204e['total_hours']
    if flight_0_100_stats_yv204e['total_fuel']:
        total_consumed_liters_yv204e += flight_0_100_stats_yv204e['total_fuel']
    if flight_0_100_stats_yv206e['total_hours']:
        total_flight_hours_yv206e += flight_0_100_stats_yv206e['total_hours']
    if flight_0_100_stats_yv206e['total_fuel']:
        total_consumed_liters_yv206e += flight_0_100_stats_yv206e['total_fuel']
    
    if flight_100_120_stats_yv204e['total_hours']:
        total_flight_hours_yv204e += flight_100_120_stats_yv204e['total_hours']
    if flight_100_120_stats_yv204e['total_fuel']:
        total_consumed_liters_yv204e += flight_100_120_stats_yv204e['total_fuel']
    if flight_100_120_stats_yv206e['total_hours']:
        total_flight_hours_yv206e += flight_100_120_stats_yv206e['total_hours']
    if flight_100_120_stats_yv206e['total_fuel']:
        total_consumed_liters_yv206e += flight_100_120_stats_yv206e['total_fuel']
    
    if flight_120_170_stats_yv204e['total_hours']:
        total_flight_hours_yv204e += flight_120_170_stats_yv204e['total_hours']
    if flight_120_170_stats_yv204e['total_fuel']:
        total_consumed_liters_yv204e += flight_120_170_stats_yv204e['total_fuel']
    if flight_120_170_stats_yv206e['total_hours']:
        total_flight_hours_yv206e += flight_120_170_stats_yv206e['total_hours']
    if flight_120_170_stats_yv206e['total_fuel']:
        total_consumed_liters_yv206e += flight_120_170_stats_yv206e['total_fuel']
    
    # Calculate fuel gallons consumed
    if total_consumed_liters_yv204e > 0:
        total_consumed_gallons_yv204e = total_consumed_liters_yv204e / Decimal('3.78541')
    if total_consumed_liters_yv206e > 0:
        total_consumed_gallons_yv206e = total_consumed_liters_yv206e / Decimal('3.78541')
    
    # Calculate fuel rate (flight hours / consumed fuel)
    if total_flight_hours_yv204e > 0:
        fuel_rate_liters_yv204e = total_consumed_liters_yv204e / total_flight_hours_yv204e
        fuel_rate_gallons_yv204e = total_consumed_gallons_yv204e / total_flight_hours_yv204e
    if total_flight_hours_yv206e > 0:
        fuel_rate_liters_yv206e = total_consumed_liters_yv206e / total_flight_hours_yv206e
        fuel_rate_gallons_yv206e = total_consumed_gallons_yv206e / total_flight_hours_yv206e

    # Calculate total flight hours and fuel cost
    total_flight_hours = total_flight_hours_yv204e + total_flight_hours_yv206e
    total_flight_hours_dollars_yv204e = total_flight_hours_yv204e * hourly_rate_yv204e
    total_flight_hours_dollars_yv206e = total_flight_hours_yv206e * hourly_rate_yv206e
    total_flight_hours_dollars = total_flight_hours_dollars_yv204e + total_flight_hours_dollars_yv206e
    total_fuel_cost_yv204e = total_consumed_liters_yv204e * fuel_cost_yv204e
    total_fuel_cost_yv206e = total_consumed_liters_yv206e * fuel_cost_yv206e
    total_fuel_cost = total_fuel_cost_yv204e + total_fuel_cost_yv206e
    total_consumed_liters = total_consumed_liters_yv204e + total_consumed_liters_yv206e
    total_consumed_gallons = total_consumed_gallons_yv204e + total_consumed_gallons_yv206e
    total_cost = total_flight_hours_dollars + total_fuel_cost
    
    # Calculate flight hour cost (cost per hour) - handle division by zero
    if total_flight_hours_yv204e > 0:
        flight_hour_cost_yv204e = (total_flight_hours_dollars_yv204e + total_fuel_cost_yv204e) / total_flight_hours_yv204e
    if total_flight_hours_yv206e > 0:
        flight_hour_cost_yv206e = (total_flight_hours_dollars_yv206e + total_fuel_cost_yv206e) / total_flight_hours_yv206e

    if role_type == 'instructor' and instructor_hourly_rate is not None:
        total_paid_to_instructor_yv204e = total_flight_hours_yv204e * instructor_hourly_rate
        total_paid_to_instructor_yv206e = total_flight_hours_yv206e * instructor_hourly_rate
        total_paid_to_instructor = total_paid_to_instructor_yv204e + total_paid_to_instructor_yv206e

    return {
        'total_flight_hours_yv204e': total_flight_hours_yv204e,
        'total_flight_hours_yv206e': total_flight_hours_yv206e,
        'total_flight_hours': total_flight_hours,
        'total_flight_hours_dollars_yv204e': total_flight_hours_dollars_yv204e,
        'total_flight_hours_dollars_yv206e': total_flight_hours_dollars_yv206e,
        'total_flight_hours_dollars': total_flight_hours_dollars,
        'total_fuel_cost_yv204e': total_fuel_cost_yv204e,
        'total_fuel_cost_yv206e': total_fuel_cost_yv206e,
        'total_fuel_cost': total_fuel_cost,
        'total_consumed_liters': total_consumed_liters,
        'total_consumed_liters_yv204e': total_consumed_liters_yv204e,
        'total_consumed_liters_yv206e': total_consumed_liters_yv206e,
        'total_consumed_gallons': total_consumed_gallons,
        'total_consumed_gallons_yv204e': total_consumed_gallons_yv204e,
        'total_consumed_gallons_yv206e': total_consumed_gallons_yv206e,
        'fuel_rate_liters_yv204e': fuel_rate_liters_yv204e,
        'fuel_rate_liters_yv206e': fuel_rate_liters_yv206e,
        'fuel_rate_gallons_yv204e': fuel_rate_gallons_yv204e,
        'fuel_rate_gallons_yv206e': fuel_rate_gallons_yv206e,
        'total_cost': total_cost,
        'flight_hour_cost_yv204e': flight_hour_cost_yv204e,
        'flight_hour_cost_yv206e': flight_hour_cost_yv206e,
        'total_paid_to_instructor_yv204e': total_paid_to_instructor_yv204e,
        'total_paid_to_instructor_yv206e': total_paid_to_instructor_yv206e,
        'total_paid_to_instructor': total_paid_to_instructor,
    }

@login_required
def student_stats_page(request, student_id=None):
    """Display statistics page for a student."""
    from fleet.models import Aircraft
    from accounts.models import StudentProfile
    
    user = request.user
    
    # If student_id is provided, staff is viewing another student's stats
    if student_id:
        if user.role != 'STAFF':
            messages.error(request, 'Acceso no autorizado')
            return redirect('dashboard:dashboard')
        try:
            student = User.objects.get(national_id=student_id, role='STUDENT')
            student_profile = StudentProfile.objects.get(user=student)
            student_hourly_rate = student_profile.flight_rate
            user_id = student_id
        except User.DoesNotExist:
            messages.error(request, 'Estudiante no encontrado')
            return redirect('fms:user_stats_page')
        except StudentProfile.DoesNotExist:
            messages.error(request, 'Perfil de estudiante no encontrado')
            return redirect('fms:user_stats_page')
    else:
        # User viewing their own stats
        user_id = user.national_id
        student = None

        try:
            student_profile = StudentProfile.objects.get(user=user)
            student_hourly_rate = student_profile.flight_rate
        except StudentProfile.DoesNotExist:
            messages.error(request, 'Perfil de estudiante no encontrado')
            return redirect('dashboard:dashboard')

        # Check user role and selected role (for staff who are also students)
        selected_role = request.session.get('selected_role', None)
        is_student = user.role == 'STUDENT' or selected_role == 'STUDENT'
        
        # Only allow students (by role or selected role)
        if not is_student:
            messages.error(request, 'Acceso no autorizado')
            return redirect('dashboard:dashboard')

    try:
        stats = calculate_user_stats(user_id, 'student', None, student_hourly_rate)
    except Aircraft.DoesNotExist:
        messages.error(request, 'Aeronave no encontrada')
        if student_id:
            return redirect('fms:user_stats_page')
        return redirect('dashboard:dashboard')

    context = {
        'student': student,
        'total_flight_hours_yv204e': round(stats['total_flight_hours_yv204e'], 1),
        'total_flight_hours_yv206e': round(stats['total_flight_hours_yv206e'], 1),
        'total_flight_hours': round(stats['total_flight_hours'], 1),
        'total_flight_hours_dollars_yv204e': round(stats['total_flight_hours_dollars_yv204e'], 1),
        'total_flight_hours_dollars_yv206e': round(stats['total_flight_hours_dollars_yv206e'], 1),
        'total_flight_hours_dollars': round(stats['total_flight_hours_dollars'], 1),
        'total_fuel_cost_yv204e': round(stats['total_fuel_cost_yv204e'], 1),
        'total_fuel_cost_yv206e': round(stats['total_fuel_cost_yv206e'], 1),
        'total_fuel_cost': round(stats['total_fuel_cost'], 1),
        'total_consumed_liters': round(stats['total_consumed_liters'], 1),
        'total_consumed_liters_yv204e': round(stats['total_consumed_liters_yv204e'], 1),
        'total_consumed_liters_yv206e': round(stats['total_consumed_liters_yv206e'], 1),
        'total_consumed_gallons': round(stats['total_consumed_gallons'], 1),
        'total_consumed_gallons_yv204e': round(stats['total_consumed_gallons_yv204e'], 1),
        'total_consumed_gallons_yv206e': round(stats['total_consumed_gallons_yv206e'], 1),
        'fuel_rate_liters_yv204e': round(stats['fuel_rate_liters_yv204e'], 1),
        'fuel_rate_liters_yv206e': round(stats['fuel_rate_liters_yv206e'], 1),
        'fuel_rate_gallons_yv204e': round(stats['fuel_rate_gallons_yv204e'], 1),
        'fuel_rate_gallons_yv206e': round(stats['fuel_rate_gallons_yv206e'], 1),
        'total_cost': round(stats['total_cost'], 1),
        'flight_hour_cost_yv204e': round(stats['flight_hour_cost_yv204e'], 1),
        'flight_hour_cost_yv206e': round(stats['flight_hour_cost_yv206e'], 1),
    }
    return render(request, 'fms/student_stats.html', context)

@login_required
def instructor_stats_page(request, instructor_id=None):
    """Display statistics page for an instructor."""
    from fleet.models import Aircraft
    from accounts.models import InstructorProfile
    
    user = request.user
    
    # If instructor_id is provided, staff is viewing another instructor's stats
    if instructor_id:
        if user.role != 'STAFF':
            messages.error(request, 'Acceso no autorizado')
            return redirect('dashboard:dashboard')
        try:
            instructor = User.objects.get(national_id=instructor_id, role='INSTRUCTOR')
            instructor_profile = InstructorProfile.objects.get(user=instructor)
            instructor_hourly_rate = instructor_profile.instructor_hourly_rate
            user_id = instructor_id
        except User.DoesNotExist:
            messages.error(request, 'Instructor no encontrado')
            return redirect('fms:user_stats_page')
        except InstructorProfile.DoesNotExist:
            messages.error(request, 'Perfil de instructor no encontrado')
            return redirect('fms:user_stats_page')
    else:
        # User viewing their own stats
        user_id = user.national_id
        instructor = None
        
        try:
            instructor_profile = InstructorProfile.objects.get(user=user)
            instructor_hourly_rate = instructor_profile.instructor_hourly_rate
        except InstructorProfile.DoesNotExist:
            messages.error(request, 'Perfil de instructor no encontrado')
            return redirect('dashboard:dashboard')
        
        # Check user role and selected role (for staff who are also instructors)
        selected_role = request.session.get('selected_role', None)
        is_instructor = user.role == 'INSTRUCTOR' or selected_role == 'INSTRUCTOR'
        
        # Only allow instructors (by role or selected role)
        if not is_instructor:
            messages.error(request, 'Acceso no autorizado')
            return redirect('dashboard:dashboard')

    try:
        stats = calculate_user_stats(user_id, 'instructor', instructor_hourly_rate, None)
    except Aircraft.DoesNotExist:
        messages.error(request, 'Aeronave no encontrada')
        if instructor_id:
            return redirect('fms:user_stats_page')
        return redirect('dashboard:dashboard')

    context = {
        'instructor': instructor,
        'total_flight_hours_yv204e': round(stats['total_flight_hours_yv204e'], 1),
        'total_flight_hours_yv206e': round(stats['total_flight_hours_yv206e'], 1),
        'total_flight_hours': round(stats['total_flight_hours'], 1),
        'total_flight_hours_dollars_yv204e': round(stats['total_flight_hours_dollars_yv204e'], 1),
        'total_flight_hours_dollars_yv206e': round(stats['total_flight_hours_dollars_yv206e'], 1),
        'total_flight_hours_dollars': round(stats['total_flight_hours_dollars'], 1),
        'total_fuel_cost_yv204e': round(stats['total_fuel_cost_yv204e'], 1),
        'total_fuel_cost_yv206e': round(stats['total_fuel_cost_yv206e'], 1),
        'total_fuel_cost': round(stats['total_fuel_cost'], 1),
        'total_consumed_liters': round(stats['total_consumed_liters'], 1),
        'total_consumed_liters_yv204e': round(stats['total_consumed_liters_yv204e'], 1),
        'total_consumed_liters_yv206e': round(stats['total_consumed_liters_yv206e'], 1),
        'total_consumed_gallons': round(stats['total_consumed_gallons'], 1),
        'total_consumed_gallons_yv204e': round(stats['total_consumed_gallons_yv204e'], 1),
        'total_consumed_gallons_yv206e': round(stats['total_consumed_gallons_yv206e'], 1),
        'fuel_rate_liters_yv204e': round(stats['fuel_rate_liters_yv204e'], 1),
        'fuel_rate_liters_yv206e': round(stats['fuel_rate_liters_yv206e'], 1),
        'fuel_rate_gallons_yv204e': round(stats['fuel_rate_gallons_yv204e'], 1),
        'fuel_rate_gallons_yv206e': round(stats['fuel_rate_gallons_yv206e'], 1),
        'total_cost': round(stats['total_cost'], 1),
        'flight_hour_cost_yv204e': round(stats['flight_hour_cost_yv204e'], 1),
        'flight_hour_cost_yv206e': round(stats['flight_hour_cost_yv206e'], 1),
        'total_paid_to_instructor_yv204e': round(stats['total_paid_to_instructor_yv204e'], 1),
        'total_paid_to_instructor_yv206e': round(stats['total_paid_to_instructor_yv206e'], 1),
        'total_paid_to_instructor': round(stats['total_paid_to_instructor'], 1),
    }
    if instructor_id:
        return render(request, 'fms/instructor_stats.html', context)
    else:
        return render(request, 'fms/instructor_stats_limited.html', context)

@login_required
def user_stats_page(request):
    """Display a page listing all students and instructors with their stats."""
    # Only allow staff
    if request.user.role != 'STAFF':
        messages.error(request, 'Acceso no autorizado')
        return redirect('dashboard:dashboard')
    
    # Get all students and instructors
    students = StudentProfile.objects.select_related('user').order_by('user__last_name', 'user__first_name')
    instructors = InstructorProfile.objects.select_related('user').order_by('user__last_name', 'user__first_name')
    
    context = {
        'students': students,
        'instructors': instructors,
    }
    return render(request, 'fms/user_stats.html', context)

def fleet_flights_page(request):
    """Display a page listing all flights and flight reports for the fleet."""
    from fleet.models import Aircraft
    from .models import FlightEvaluation0_100, FlightEvaluation100_120, FlightEvaluation120_170, FlightReport
    
    yv204e = Aircraft.objects.get(registration='YV204E')
    yv206e = Aircraft.objects.get(registration='YV206E')

    flights_yv204e_0_100 = FlightEvaluation0_100.objects.filter(aircraft=yv204e).order_by('-session_date')[:50]
    flights_yv204e_100_120 = FlightEvaluation100_120.objects.filter(aircraft=yv204e).order_by('-session_date')[:50]
    flights_yv204e_120_170 = FlightEvaluation120_170.objects.filter(aircraft=yv204e).order_by('-session_date')[:50]
    flights_yv204e_reports = FlightReport.objects.filter(aircraft=yv204e).order_by('-flight_date')[:50]

    flights_yv206e_0_100 = FlightEvaluation0_100.objects.filter(aircraft=yv206e).order_by('-session_date')[:50]
    flights_yv206e_100_120 = FlightEvaluation100_120.objects.filter(aircraft=yv206e).order_by('-session_date')[:50]
    flights_yv206e_120_170 = FlightEvaluation120_170.objects.filter(aircraft=yv206e).order_by('-session_date')[:50]
    flights_yv206e_reports = FlightReport.objects.filter(aircraft=yv206e).order_by('-flight_date')[:50]

    training_flights_yv204e = []
    for flight in flights_yv204e_0_100:
        training_flights_yv204e.append(flight)
    for flight in flights_yv204e_100_120:
        training_flights_yv204e.append(flight)
    for flight in flights_yv204e_120_170:
        training_flights_yv204e.append(flight)
    # Sort by session_date in descending order (most recent first)
    training_flights_yv204e.sort(key=lambda x: x.session_date, reverse=True)

    training_flights_yv206e = []
    for flight in flights_yv206e_0_100:
        training_flights_yv206e.append(flight)
    for flight in flights_yv206e_100_120:
        training_flights_yv206e.append(flight)
    for flight in flights_yv206e_120_170:
        training_flights_yv206e.append(flight)
    # Sort by session_date in descending order (most recent first)
    training_flights_yv206e.sort(key=lambda x: x.session_date, reverse=True)

    other_flight_yv204e = []
    for flight in flights_yv204e_reports:
        other_flight_yv204e.append(flight)
    other_flight_yv206e = []
    for flight in flights_yv206e_reports:
        other_flight_yv206e.append(flight)
    
    context = {
        'training_flights_yv204e': training_flights_yv204e,
        'training_flights_yv206e': training_flights_yv206e,
        'other_flight_yv204e': other_flight_yv204e,
        'other_flight_yv206e': other_flight_yv206e,
    }
    return render(request, 'fms/fleet_flights.html', context)

def calculate_aircraft_stats(aircraft_id):
    """
    Helper function to calculate statistics for a specific aircraft.
    
    Args:
        aircraft_id: The id of the aircraft
    Returns:
        Dictionary with all calculated statistics.
    
    Raises:
        Aircraft.DoesNotExist if the aircraft is not found.
    """
    from fleet.models import Aircraft
    
    # Get aircraft data
    aircraft = Aircraft.objects.get(id=aircraft_id)
    hourly_rate = aircraft.hourly_rate
    fuel_cost = aircraft.fuel_cost

    # Initialize totals
    total_flight_hours = Decimal('0.0')
    total_consumed_liters = Decimal('0.0')
    total_consumed_gallons = Decimal('0.0')
    fuel_rate_liters = Decimal('0.0')
    fuel_rate_gallons = Decimal('0.0')
    total_flight_hours_dollars = Decimal('0.0')
    total_fuel_cost = Decimal('0.0')
    total_cost = Decimal('0.0')
    flight_hour_cost = Decimal('0.0')
    
    # Sum flight hours and fuel from all three evaluation types
    flight_0_100_stats = FlightEvaluation0_100.objects.filter(aircraft=aircraft).aggregate(
        total_hours=Sum('session_flight_hours'),
        total_fuel=Sum('fuel_consumed')
    )
    flight_100_120_stats = FlightEvaluation100_120.objects.filter(aircraft=aircraft).aggregate(
        total_hours=Sum('session_flight_hours'),
        total_fuel=Sum('fuel_consumed')
    )
    
    flight_120_170_stats = FlightEvaluation120_170.objects.filter(aircraft=aircraft).aggregate(
        total_hours=Sum('session_flight_hours'),
        total_fuel=Sum('fuel_consumed')
    )

    flight_reports_stats = FlightReport.objects.filter(aircraft=aircraft).aggregate(
        total_hours=Sum('flight_hours'),
        total_fuel=Sum('fuel_consumed')
    )
    
    # Add up all the totals
    if flight_0_100_stats['total_hours']:
        total_flight_hours += flight_0_100_stats['total_hours']
    if flight_0_100_stats['total_fuel']:
        total_consumed_liters += flight_0_100_stats['total_fuel']

    if flight_100_120_stats['total_hours']:
        total_flight_hours += flight_100_120_stats['total_hours']
    if flight_100_120_stats['total_fuel']:
        total_consumed_liters += flight_100_120_stats['total_fuel']
    
    if flight_120_170_stats['total_hours']:
        total_flight_hours += flight_120_170_stats['total_hours']
    if flight_120_170_stats['total_fuel']:
        total_consumed_liters += flight_120_170_stats['total_fuel']

    if flight_reports_stats['total_hours']:
        total_flight_hours += flight_reports_stats['total_hours']
    if flight_reports_stats['total_fuel']:
        total_consumed_liters += flight_reports_stats['total_fuel']
    
    # Calculate fuel gallons consumed
    if total_consumed_liters > 0:
        total_consumed_gallons = total_consumed_liters / Decimal('3.78541')
    
    # Calculate fuel rate (flight hours / consumed fuel)
    if total_flight_hours > 0:
        fuel_rate_liters = total_consumed_liters / total_flight_hours
        fuel_rate_gallons = total_consumed_gallons / total_flight_hours

    # Calculate total flight hours and fuel cost
    total_flight_hours_dollars = total_flight_hours * hourly_rate
    total_fuel_cost = total_consumed_liters * fuel_cost
    total_cost = total_flight_hours_dollars + total_fuel_cost
    
    # Calculate flight hour cost (cost per hour) - handle division by zero
    if total_flight_hours > 0:
        flight_hour_cost = total_cost / total_flight_hours

    return {
        'total_flight_hours': total_flight_hours,
        'total_flight_hours_dollars': total_flight_hours_dollars,
        'total_fuel_cost': total_fuel_cost,
        'total_consumed_liters': total_consumed_liters,
        'total_consumed_gallons': total_consumed_gallons,
        'fuel_rate_liters': fuel_rate_liters,
        'fuel_rate_gallons': fuel_rate_gallons,
        'total_cost': total_cost,
        'flight_hour_cost': flight_hour_cost,
    }

@login_required
def fleet_stats_page(request, aircraft_registration):
    """Display statistics page for a specific aircraft."""
    from fleet.models import Aircraft
    
    try:
        aircraft = Aircraft.objects.get(registration=aircraft_registration)
        stats = calculate_aircraft_stats(aircraft.id)
        
        context = {
            'aircraft': aircraft,
            'total_flight_hours': round(stats['total_flight_hours'], 1),
            'total_flight_hours_dollars': round(stats['total_flight_hours_dollars'], 1),
            'total_fuel_cost': round(stats['total_fuel_cost'], 1),
            'total_consumed_liters': round(stats['total_consumed_liters'], 1),
            'total_consumed_gallons': round(stats['total_consumed_gallons'], 1),
            'fuel_rate_liters': round(stats['fuel_rate_liters'], 1),
            'fuel_rate_gallons': round(stats['fuel_rate_gallons'], 1),
            'total_cost': round(stats['total_cost'], 1),
            'flight_hour_cost': round(stats['flight_hour_cost'], 1),
        }
        return render(request, 'fms/aircraft_stats.html', context)
    except Aircraft.DoesNotExist:
        messages.error(request, 'Aeronave no encontrada')
        return redirect('fms:fleet_flights_page')
