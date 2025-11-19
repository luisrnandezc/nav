import os
import json
from types import SimpleNamespace
from django.shortcuts import render, redirect, get_object_or_404
from openai import OpenAI
from .forms import SMSVoluntaryReportForm, SMSAnalysisEditForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import ReportAnalysis, VoluntaryReport, SMSAction
from django.conf import settings


@login_required
def main_sms(request):
    """
    A view to handle the SMS main page.
    """
    # Get reports count for the gauge
    reports_count = VoluntaryReport.objects.count()
    
    # Get pending SMS actions
    pending_actions = SMSAction.objects.filter(status='PENDING').select_related('report__report', 'assigned_to').order_by('-created_at')[:10]
    
    context = {
        'can_manage_sms': request.user.has_perm('accounts.can_manage_sms'),
        'reports_count': reports_count,
        'pending_actions': pending_actions,
    }
    return render(request, 'sms/main_sms.html', context)

def voluntary_report(request):
    """
    A view to handle the SMS voluntary report.
    """

    if request.method == 'POST':
        is_anonymous = request.POST.get('is_anonymous') == 'YES'

        if is_anonymous or not request.user.is_authenticated:
            form = SMSVoluntaryReportForm(request.POST)
        else:
            form = SMSVoluntaryReportForm(request.POST, user=request.user)

        if form.is_valid():
            try:
                form.save()
                return redirect('dashboard:dashboard')
            except Exception as e:
                messages.error(request, f'Error al guardar el reporte: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        if request.user.is_authenticated:
            form = SMSVoluntaryReportForm(user=request.user)
        else:
            form = SMSVoluntaryReportForm()

    return render(request, 'sms/voluntary_report.html', {'form': form})

def run_sms_voluntary_report_analysis(report):
    """
    A function to run the AI analysis for the SMS voluntary report.
    
    Args:
        report (VoluntaryReport): The report to analyze
    """
    import logging
    import sys
    
    # Set up logging to both file and console
    log_file_path = os.path.join(settings.BASE_DIR, 'sms/logs/sms_analysis.log')
    
    # Create logger
    logger = logging.getLogger('sms_analysis')
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # File handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler (for PythonAnywhere Always-On Task)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter('[LOG] %(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    logger.info("=" * 80)
    logger.info("Starting run_sms_voluntary_report_analysis for report ID: {}".format(report.id))

    # Set SMS prompt
    base_prompt = settings.SMS_PROMPT
    logger.info("SMS_PROMPT loaded, length: {} characters".format(len(base_prompt)))

    # Create a SimpleNamespace object to support {report.date} syntax in the prompt
    report_ns = SimpleNamespace(
        date=getattr(report, "date", "") or "",
        time=getattr(report, "time", "") or "",
        area=getattr(report, "area", "") or "",
        description=getattr(report, "description", "") or ""
    )
    logger.info("Report namespace created - date: {}, time: {}, area: {}, description length: {}".format(
        report_ns.date, report_ns.time, report_ns.area, len(report_ns.description)
    ))

    rendered_prompt = base_prompt.format(report=report_ns)
    logger.info("Rendered prompt length: {} characters".format(len(rendered_prompt)))

    # Retrieve the API key from environment variables
    logger.info("Retrieving OPENAI_API_KEY from environment variables")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        error_msg = "Error: OpenAI API key not found in environment variables."
        logger.error(error_msg)
        print("[ERROR] {}".format(error_msg))
        return error_msg
    
    logger.info("API key retrieved successfully (length: {} characters)".format(len(api_key) if api_key else 0))

    try:
        logger.info("Attempting to initialize OpenAI client")
        
        # Initialize the OpenAI client with the retrieved key
        client = OpenAI(api_key=api_key)
        
        logger.info("OpenAI client initialized successfully")

        # Make a request to the responses endpoint
        logger.info("Making API request to OpenAI responses endpoint")
        logger.info("Model: gpt-5-nano, reasoning: medium, text verbosity: medium")
        
        response = client.responses.create(
            model="gpt-5-nano",
            reasoning = {"effort": "medium"},
            text = {"verbosity": "medium"},
            instructions = base_prompt,
            input=rendered_prompt,
        )
        
        logger.info("API request completed successfully")
        
        # Extract the content from the response
        content = response.output_text
        logger.info("Response content extracted, length: {} characters".format(len(content) if content else 0))
        
        logger.info("=" * 80)
        return content
        
    except TypeError as e:
        error_msg = "TypeError during OpenAI operation: {}".format(str(e))
        logger.error(error_msg, exc_info=True)
        print("[ERROR] {}".format(error_msg))
        import traceback
        logger.error("Full traceback: {}".format(traceback.format_exc()))
        logger.info("=" * 80)
        return "API key validation failed. Error: {}".format(e)
    except AttributeError as e:
        error_msg = "AttributeError during OpenAI operation: {}".format(str(e))
        logger.error(error_msg, exc_info=True)
        print("[ERROR] {}".format(error_msg))
        import traceback
        logger.error("Full traceback: {}".format(traceback.format_exc()))
        logger.info("=" * 80)
        return "API key validation failed. Error: {}".format(e)
    except Exception as e:
        error_msg = "Exception during OpenAI operation: {} (Type: {})".format(str(e), type(e).__name__)
        logger.error(error_msg, exc_info=True)
        print("[ERROR] {}".format(error_msg))
        import traceback
        logger.error("Full traceback: {}".format(traceback.format_exc()))
        logger.info("=" * 80)
        return "API key validation failed. Error: {}".format(e)
    
@login_required
def report_list(request):
    """
    Display the report list page for the current user.
    """
    user = request.user
    
    # Fetch grade logs for the student (last 10)
    reports = ReportAnalysis.objects.order_by('-created_at')[:10]
    
    context = {
        'reports': reports,
    }
    
    return render(request, 'sms/report_list.html', context)

@login_required
def report_detail(request, report_id):
    """
    Display the report detail page for the given report ID.
    Allow editing of AI analysis fields.
    """
    report = ReportAnalysis.objects.get(id=report_id)
    
    if request.method == 'POST':
        form = SMSAnalysisEditForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            return redirect('sms:report_list')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = SMSAnalysisEditForm(instance=report)
    
    context = {
        'report': report,
        'form': form,
    }
    
    return render(request, 'sms/report_detail.html', context)


# Risk Management Views
@login_required
@require_http_methods(["POST"])
def delete_risk_item(request, report_id, item_index):
    """Delete a specific risk item"""
    try:
        report = get_object_or_404(ReportAnalysis, id=report_id)
        risk_analysis = list(report.risk_analysis)
        
        if 0 <= item_index < len(risk_analysis):
            risk_analysis.pop(item_index)
            report.risk_analysis = risk_analysis
            report.save()
            return JsonResponse({'success': True, 'message': 'Risk deleted successfully'})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid item index'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_risk_item(request, report_id):
    """Add a new risk item"""
    try:
        report = get_object_or_404(ReportAnalysis, id=report_id)
        data = json.loads(request.body)
        
        new_risk = {
            'relevance': data.get('relevance', 'medium'),
            'text': data.get('text', '')
        }
        
        risk_analysis = list(report.risk_analysis)
        risk_analysis.append(new_risk)
        report.risk_analysis = risk_analysis
        report.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Risk added successfully',
            'new_index': len(risk_analysis) - 1
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# Recommendation Management Views
@login_required
@require_http_methods(["POST"])
def delete_recommendation_item(request, report_id, item_index):
    """Delete a specific recommendation item"""
    try:
        report = get_object_or_404(ReportAnalysis, id=report_id)
        recommendations = list(report.recommendations)
        
        if 0 <= item_index < len(recommendations):
            recommendations.pop(item_index)
            report.recommendations = recommendations
            report.save()
            return JsonResponse({'success': True, 'message': 'Recommendation deleted successfully'})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid item index'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_recommendation_item(request, report_id):
    """Add a new recommendation item"""
    try:
        report = get_object_or_404(ReportAnalysis, id=report_id)
        data = json.loads(request.body)
        
        new_recommendation = {
            'relevance': data.get('relevance', 'medium'),
            'text': data.get('text', '')
        }
        
        recommendations = list(report.recommendations)
        recommendations.append(new_recommendation)
        report.recommendations = recommendations
        report.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Recommendation added successfully',
            'new_index': len(recommendations) - 1
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def create_actions_from_recommendations(request, report_id):
    """
    Create SMSAction objects from the recommendations of a ReportAnalysis.
    """
    try:
        # Get the report analysis
        report_analysis = ReportAnalysis.objects.get(id=report_id)
        
        # Check if user has permission to manage SMS
        if not request.user.has_perm('accounts.can_manage_sms'):
            messages.error(request, 'No tiene permisos para crear acciones.')
            return redirect('sms:report_detail', report_id=report_id)
        
        # Check if actions have already been created
        if report_analysis.actions_created:
            messages.warning(request, 'Las acciones ya han sido creadas para este reporte.')
            return redirect('sms:report_detail', report_id=report_id)
        
        # Create actions from recommendations
        actions_created = SMSAction.create_actions_from_recommendations(report_analysis)
        
        if actions_created:
            messages.success(request, f'Se crearon {len(actions_created)} acciones exitosamente.')
        else:
            messages.info(request, 'No hay recomendaciones para crear acciones.')
        
        return redirect('sms:report_detail', report_id=report_id)
        
    except ReportAnalysis.DoesNotExist:
        messages.error(request, 'El análisis de reporte no existe.')
        return redirect('sms:report_list')
    except Exception as e:
        messages.error(request, f'Error al crear acciones: {str(e)}')
        return redirect('sms:report_detail', report_id=report_id)
