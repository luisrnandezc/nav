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
def main_sms(request):
    """
    A view to handle the SMS main page.
    """
    # Get reports count for the gauge
    reports_count = VoluntaryHazardReport.objects.count()
    
    context = {
        'can_manage_sms': request.user.has_perm('accounts.can_manage_sms'),
        'reports_count': reports_count,
    }
    return render(request, 'sms/main_sms.html', context)

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

    return render(request, 'sms/voluntary_hazard_report.html', {'form': form})

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
        logger.info("Model: gpt-5, reasoning: high, text verbosity: high")
        
        response = client.responses.create(
            model="gpt-5",
            reasoning = {"effort": "high"},
            text = {"verbosity": "high"},
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