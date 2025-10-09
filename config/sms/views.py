import os
from django.shortcuts import render, redirect
from openai import OpenAI
from .forms import SMSVoluntaryReportForm, SMSAnalysisEditForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import ReportAnalysis

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

def run_sms_voluntary_report_analysis(custom_prompt=None):
    """
    A function to run the SMS voluntary report analysis.
    
    Args:
        custom_prompt (str, optional): Custom prompt for voluntary report analysis
    """
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
            instructions = (
                """
                "Eres un experto en SMS (Safety Management System) y estás encargado de "
                "analizar reportes de seguridad operacional para una escuela de aviación. "
                "Debes ejercer tu función de analista tomando como base los siguientes documentos: "

                "1. Anexo 19 de la OACI "
                "2. Documento 9859 de la OACI "

                "Así mismo, toma en consideración los siguientes factores: "

                "1. La escuela utiliza dos aeronaves marca Piper, un PA-28-161 y un PA-28-235. "
                "2. Es una escuela pequeña con un equipo de 8 personas y 3 instructores de vuelo."
                "3. Las recomendaciones deben ser específicas, realistas y ajustadas al tamaño de la escuela. "
                "4. Utiliza un tono formal y profesional. "

                "IMPORTANTE: Responde ÚNICAMENTE con un JSON válido. NO incluyas texto explicativo antes o después del JSON. "
                " "risk_analysis" y "recommendations" deben ser arreglos de objetos, no strings. "
                "El JSON debe tener exactamente esta estructura: "
                    [ 
                        {
                            "is_valid": "SI",
                            "severity": "C",
                            "probability": "3", 
                            "value": "C3",
                            "risk_analysis": [
                                {"relevance": "high", "text": "Riesgo 1"},
                                {"relevance": "medium", "text": "Riesgo 2"},
                                {"relevance": "low", "text": "Riesgo 3"}
                            ],
                            "recommendations": [
                                {"relevance": "high", "text": "Recomendación 1"},
                                {"relevance": "medium", "text": "Recomendación 2"},
                                {"relevance": "low", "text": "Recomendación 3"}
                            ]
                        } 
                    ]
                "NOTA: Reemplaza los valores de ejemplo con los valores reales para este reporte específico."
            """),
            input=custom_prompt,
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
