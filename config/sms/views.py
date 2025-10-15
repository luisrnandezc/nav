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
from .models import ReportAnalysis
from django.conf import settings


@login_required
def main_sms(request):
    """
    A view to handle the SMS main page.
    """
    context = {
        'can_manage_sms': request.user.has_perm('accounts.can_manage_sms'),
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

    # Set SMS prompt
    base_prompt = settings.SMS_PROMPT

    # Create a SimpleNamespace object to support {report.date} syntax in the prompt
    report_ns = SimpleNamespace(
        date=getattr(report, "date", "") or "",
        time=getattr(report, "time", "") or "",
        area=getattr(report, "area", "") or "",
        description=getattr(report, "description", "") or ""
    )

    rendered_prompt = base_prompt.format(report=report_ns)

    # Retrieve the API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Error: OpenAI API key not found in environment variables."

    try:
        # Initialize the OpenAI client with the retrieved key
        client = OpenAI(api_key=api_key)

        # Make a request to the responses endpoint
        response = client.responses.create(
            model="gpt-5-nano",
            reasoning = {"effort": "medium"},
            text = {"verbosity": "medium"},
            instructions = base_prompt,
            input=rendered_prompt,
        )
        # Extract the content from the response
        content = response.output_text
        return content
        
    except Exception as e:
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
            messages.success(request, 'Análisis actualizado exitosamente.')
            return redirect('sms:report_detail', report_id=report_id)
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
