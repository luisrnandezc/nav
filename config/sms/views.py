import os
import json
from types import SimpleNamespace
from django.shortcuts import render, redirect, get_object_or_404
from openai import OpenAI
from .forms import SMSVoluntaryHazardReportForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import VoluntaryHazardReport
from django.conf import settings
import logging
import sys


@login_required
def sms_dashboard(request):
    """
    A view to handle the SMS main page.
    """
    # Get all voluntary hazard reports ordered by most recent first
    voluntary_reports = VoluntaryHazardReport.objects.all().order_by('-created_at')
    
    context = {
        'can_manage_sms': request.user.has_perm('accounts.can_manage_sms'),
        'voluntary_reports': voluntary_reports,
    }
    return render(request, 'sms/sms_dashboard.html', context)

@login_required
def voluntary_hazard_report_detail(request, report_id):
    """
    A view to display the detail of a Voluntary Hazard Report.
    """
    report = get_object_or_404(VoluntaryHazardReport, id=report_id)
    
    # Parse AI analysis result if available
    ai_analysis = report.ai_analysis_result if report.ai_analysis_result else {}
    risks = ai_analysis.get('risks', {})
    actions = ai_analysis.get('actions', {})
    is_valid = ai_analysis.get('is_valid', 'NO')
    
    context = {
        'report': report,
        'ai_analysis': ai_analysis,
        'risks': risks,
        'actions': actions,
        'is_valid': is_valid,
        'can_manage_sms': request.user.has_perm('accounts.can_manage_sms'),
    }
    return render(request, 'sms/voluntary_hazard_report_detail.html', context)


@login_required
@require_http_methods(["POST"])
def delete_risk(request, report_id, risk_key):
    """
    Remove a specific risk (and its related actions) from the AI analysis payload.
    """
    report = get_object_or_404(VoluntaryHazardReport, id=report_id)

    if not request.user.has_perm('accounts.can_manage_sms'):
        messages.error(request, 'No tiene permisos para modificar este reporte.')
        return redirect('sms:voluntary_hazard_report_detail', report_id=report_id)

    ai_analysis = report.ai_analysis_result or {}
    risks = ai_analysis.get('risks', {}) or {}
    actions = ai_analysis.get('actions', {}) or {}

    if risk_key not in risks:
        messages.warning(request, 'El riesgo solicitado no existe.')
        return redirect('sms:voluntary_hazard_report_detail', report_id=report_id)

    risks.pop(risk_key, None)
    actions.pop(risk_key, None)

    ai_analysis['risks'] = risks
    ai_analysis['actions'] = actions
    report.ai_analysis_result = ai_analysis
    report.save(update_fields=['ai_analysis_result', 'updated_at'])

    messages.success(request, f'Se eliminó el {risk_key} y sus acciones asociadas.')
    return redirect('sms:voluntary_hazard_report_detail', report_id=report_id)


@login_required
@require_http_methods(["POST"])
def delete_action(request, report_id, risk_key, action_index):
    """
    Remove a single action from the AI analysis payload.
    """
    report = get_object_or_404(VoluntaryHazardReport, id=report_id)

    if not request.user.has_perm('accounts.can_manage_sms'):
        messages.error(request, 'No tiene permisos para modificar este reporte.')
        return redirect('sms:voluntary_hazard_report_detail', report_id=report_id)

    ai_analysis = report.ai_analysis_result or {}
    actions = ai_analysis.get('actions', {}) or {}

    if risk_key not in actions:
        messages.warning(request, 'Las acciones para este riesgo no existen.')
        return redirect('sms:voluntary_hazard_report_detail', report_id=report_id)

    action_list = actions.get(risk_key) or []

    try:
        action_list.pop(int(action_index))
    except (IndexError, ValueError, TypeError):
        messages.warning(request, 'La acción solicitada no existe.')
        return redirect('sms:voluntary_hazard_report_detail', report_id=report_id)

    if action_list:
        actions[risk_key] = action_list
    else:
        actions.pop(risk_key, None)

    ai_analysis['actions'] = actions
    report.ai_analysis_result = ai_analysis
    report.save(update_fields=['ai_analysis_result', 'updated_at'])

    messages.success(request, 'Se eliminó la acción seleccionada.')
    return redirect('sms:voluntary_hazard_report_detail', report_id=report_id)


@login_required
@require_http_methods(["POST"])
def add_risk(request, report_id):
    """
    Append a new risk (with evaluation and description) to the AI analysis payload.
    """
    report = get_object_or_404(VoluntaryHazardReport, id=report_id)

    if not request.user.has_perm('accounts.can_manage_sms'):
        messages.error(request, 'No tiene permisos para modificar este reporte.')
        return redirect('sms:voluntary_hazard_report_detail', report_id=report_id)

    description = (request.POST.get('description') or '').strip()
    severity = (request.POST.get('severity') or '').strip().upper()
    probability = (request.POST.get('probability') or '').strip()

    if not description:
        messages.error(request, 'La descripción del riesgo es obligatoria.')
        return redirect('sms:voluntary_hazard_report_detail', report_id=report_id)

    if severity not in ['A', 'B', 'C', 'D', 'E']:
        messages.error(request, 'Seleccione un nivel de severidad válido.')
        return redirect('sms:voluntary_hazard_report_detail', report_id=report_id)

    if probability not in ['1', '2', '3', '4', '5']:
        messages.error(request, 'Seleccione un nivel de probabilidad válido.')
        return redirect('sms:voluntary_hazard_report_detail', report_id=report_id)

    ai_analysis = report.ai_analysis_result or {}
    risks = ai_analysis.get('risks', {}) or {}

    next_index = 1
    if risks:
        existing_indexes = []
        for key in risks.keys():
            if key.startswith('risk'):
                suffix = key.replace('risk', '')
                if suffix.isdigit():
                    existing_indexes.append(int(suffix))
        next_index = max(existing_indexes, default=0) + 1

    new_risk_key = f"risk{next_index}"
    risks[new_risk_key] = {
        'description': description,
        'evaluation': f'{severity}{probability}',
    }

    ai_analysis['risks'] = risks
    report.ai_analysis_result = ai_analysis
    report.save(update_fields=['ai_analysis_result', 'updated_at'])

    messages.success(request, 'Se agregó un nuevo riesgo al análisis.')
    return redirect('sms:voluntary_hazard_report_detail', report_id=report_id)

def voluntary_hazard_report(request):
    """
    A view to handle the SMS voluntary hazard report.
    """

    if request.method == 'POST':
        is_anonymous = request.POST.get('is_anonymous') == 'YES'

        if is_anonymous or not request.user.is_authenticated:
            form = SMSVoluntaryHazardReportForm(request.POST)
        else:
            form = SMSVoluntaryHazardReportForm(request.POST, user=request.user)

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
            form = SMSVoluntaryHazardReportForm(user=request.user)
        else:
            form = SMSVoluntaryHazardReportForm()
    
    selected_role = request.session.get('selected_role', None)
    user_role = selected_role if selected_role else request.user.role

    context = {
        'form': form,
        'user_role': user_role,
    }

    return render(request, 'sms/voluntary_hazard_report.html', context)

def voluntary_hazard_report_ai_analysis_logger():
    """
    A function to set up the logger for the AI analysis of the SMS Voluntary Hazard Report (VHR).
    """
    # Set up logging to both file and console
    log_file_path = os.path.join(settings.BASE_DIR, 'sms/logs/voluntary_hazard_report_ai_analysis.log')
    
    # Create logger
    logger = logging.getLogger('voluntary_hazard_report_ai_analysis')
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
    
    return logger

def run_ai_analysis_for_voluntary_hazard_report(report):
    """
    A function to run the AI analysis for the SMS Voluntary Hazard Report (VHR).
    
    Args:
        report (VoluntaryHazardReport): The Voluntary Hazard Report (VHR) to analyze
    """

    logger = voluntary_hazard_report_ai_analysis_logger()

    logger.info("=" * 80)
    logger.info("Starting run_ai_analysis_for_voluntary_hazard_report for VHR ID: {}".format(report.id))

    # Set AI analysis prompt
    base_prompt = settings.SARA_HAZARD_ANALYSIS_PROMPT
    logger.info("AI analysis prompt loaded, length: {} characters".format(len(base_prompt)))

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

        model = "gpt-5.1"
        tools = [{"type": "web_search"}]
        reasoning = {"effort": "medium"}
        text = {"verbosity": "medium"}

        logger.info("Model: {}, reasoning: {}, text verbosity: {}, tools: {}".format(model, reasoning["effort"], text["verbosity"], tools))
        
        response = client.responses.create(
            model=model,
            tools=tools,
            reasoning = reasoning,
            text = text,
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