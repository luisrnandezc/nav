#!/usr/bin/env python
"""
AI Analysis Worker for PythonAnywhere Always-On Task
This script continuously scans the voluntary_report table for pending reports
and processes them with AI analysis.
"""

import os
import sys
import django
import time
import json
from datetime import timedelta
from django.utils import timezone

# Add Django project to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
django_dir = os.path.join(project_dir, '..', '..')
sys.path.insert(0, django_dir)

# Set Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Import Django models and functions
from sms.models import VoluntaryReport, ReportAnalysis
from sms.views import run_sms_voluntary_report_analysis


def run_ai_analysis_for_report(report):
    """
    Run AI analysis for a specific report and save results to database.
    """
    try:
        print("[{}] Processing report {}: {}".format(
            timezone.now(), report.id, report.description[:50]
        ))
        
        # Update status to PROCESSING
        report.ai_analysis_status = 'PROCESSING'
        report.save(update_fields=['ai_analysis_status'])
        # Create the AI prompt using f-string to avoid format() issues
        prompt = f"""
        "Eres un experto en SMS (Safety Management System) y estás encargado de
        analizar reportes de seguridad operacional para una escuela de aviación.
        Debes ejercer tu función de analista tomando como base los siguientes documentos:

            1. Anexo 19 de la OACI.
            2. Documento 9859 de la OACI.

        Así mismo, toma en consideración los siguientes factores:

            1. La escuela utiliza dos aeronaves marca Piper, un PA-28-161 y un PA-28-235.
            2. Es una escuela pequeña con un equipo de 8 personas y 3 instructores de vuelo.
            3. Las recomendaciones deben ser específicas, realistas y ajustadas al tamaño de la escuela.
            4. Utiliza un tono formal y profesional.

        Analiza este reporte de seguridad operacional:
        
        Fecha: {report.date}
        Hora: {report.time}
        Área: {report.area}
        Descripción: {report.description}
        
        Por favor, ejecuta las siguientes tareas:

        1. Analiza el reporte y determina si es un reporte de seguridad válido, es decir, 
        que el contenido del reporte contiene información de una condición, situación o
        suceso relacionado con la seguridad operacional. Debes ser muy estricto con este 
        criterio, por ejemplo, si el reporte es sobre un problema con uno de las pizarras 
        electrónicas usadas para dar clases, no es un reporte de seguridad válido.

        2. Si es un reporte de seguridad válido, asígnale un Nivel de Severidad y 
        un Nivel de Probabilidad de acuerdo a la siguiente escala:

            2.1 Nivel de severidad:
            - Insignificante (A)
            - Marginal (B)
            - Significativo (C)
            - Crítico (D)
            - Catastrófico (E)

            2.2 Nivel de probabilidad:
            - Improbable (1)
            - Remoto (2)
            - Probable (3)
            - Ocasional (4)
            - Frecuente (5)

            Une los valores de Severidad y Probabilidad para obtener un valor alfanumérico.

            Ejemplo: un reporte calificado como "crítico (D)" y "ocasional (4)" tiene un valor de "D4".
            Ejemplo: un reporte calificado como "marginal (B)" y "probable (3)" tiene un valor de "B3".

            2.3 Si el reporte no es válido, asigna un valor numérico de "0".

        3. Ejecuta un análisis de riesgos del reporte, considerando el valor alfanumérico asignado en el punto 2.
        Así mismo, los riesgos identificados deben ser organizados en un arreglo JSON, de la siguiente manera:

        - "relevance": uno de ["high", "medium", "low"]
        - "text": la descripción del riesgo en español con tono formal y técnico.

        El campo de "relevance" representa la relevancia del riesgo en la seguridad operacional, en función
        del evento descrito en el reporte. Por favor ordena los riesgos de mayor a menor relevancia.
        
        Ejemplo:
        [
            {{"relevance": "high", "text": "Riesgo 1"}},
            {{"relevance": "medium", "text": "Riesgo 2"}},
            {{"relevance": "low", "text": "Riesgo 3"}}
        ]

        4. Genera recomendaciones para mejorar la seguridad operacional, considerando 
        el análisis de riesgos y el valor alfanumérico asignado en el punto 2. Las recomendaciones
        deben ser específicas, realistas y ajustadas al tamaño de la escuela. Así mismo, separa
        cada una de las recomendaciones de forma clara y organizada en un arreglo JSON, de la siguiente manera:

        - "relevance": uno de ["high", "medium", "low"]
        - "text": la recomendación en español con tono formal y técnico.
        
        El campo de "relevance" representa la relevancia de la recomendación en la seguridad operacional, en función
        del evento descrito en el reporte. Por favor ordena las recomendaciones de mayor a menor relevancia.

        Ejemplo:
        [
            {{"relevance": "high", "text": "Recomendación 1"}},
            {{"relevance": "medium", "text": "Recomendación 2"}},
            {{"relevance": "low", "text": "Recomendación 3"}}
        ]

        5. Utiliza el idioma español con tono formal, profesional y lenguaje técnico.

        6. IMPORTANTE: Responde ÚNICAMENTE con un JSON válido. NO incluyas texto explicativo antes o después del JSON.
            "risk_analysis" y "recommendations" deben ser arreglos de objetos, no strings.
        
        El JSON debe tener exactamente esta estructura (el número de riesgos y recomendaciones puede ser diferente al ejemplo):
        [ 
            {{
                "is_valid": "SI",
                "severity": "C",
                "probability": "3", 
                "value": "C3",
                "risk_analysis": [
                    {{"relevance": "high", "text": "Riesgo 1"}},
                    {{"relevance": "medium", "text": "Riesgo 2"}},
                    {{"relevance": "low", "text": "Riesgo 3"}}
                ],
                "recommendations": [
                    {{"relevance": "high", "text": "Recomendación 1"}},
                    {{"relevance": "medium", "text": "Recomendación 2"}},
                    {{"relevance": "low", "text": "Recomendación 3"}}
                ]
            }} 
        ]
        
        NOTA: Reemplaza los valores de ejemplo con los valores reales para este reporte específico.
        """

        # Call OpenAI API
        response = run_sms_voluntary_report_analysis(custom_prompt=prompt)
        
        if not response or response.startswith("Error:"):
            raise Exception("OpenAI API error: {}".format(response))
        
        # Parse JSON response
        parsed_response = json.loads(response)
        
        # Handle array response - extract the first (and only) object
        if isinstance(parsed_response, list) and len(parsed_response) > 0:
            parsed_data = parsed_response[0]
        elif isinstance(parsed_response, dict):
            parsed_data = parsed_response
        else:
            raise Exception("Invalid JSON response format: expected array or object")
        
        # Create analysis record
        is_valid_value = parsed_data.get('is_valid', 'NO')
        is_valid = 'YES' if is_valid_value == 'SI' else 'NO'
        
        analysis_record = ReportAnalysis.objects.create(
            report=report,
            is_valid=is_valid,
            severity=parsed_data.get('severity', ''),
            probability=parsed_data.get('probability', ''),
            value=parsed_data.get('value', ''),
            risk_analysis=parsed_data.get('risk_analysis', []),
            recommendations=parsed_data.get('recommendations', [])
        )
        
        # Update status to COMPLETED
        report.ai_analysis_status = 'COMPLETED'
        report.save(update_fields=['ai_analysis_status'])
        
        print("[{}] Successfully completed AI analysis for report {} (Analysis ID: {})".format(
            timezone.now(), report.id, analysis_record.id
        ))
        
        return True
        
    except Exception as e:
        error_msg = "Error processing report {}: {}".format(report.id, str(e))
        print("[{}] {}".format(timezone.now(), error_msg))
        
        # Update status to FAILED
        try:
            report.ai_analysis_status = 'FAILED'
            report.save(update_fields=['ai_analysis_status'])
        except:
            pass
        
        return False


def main_worker_loop():
    """
    Main worker loop that continuously scans for pending reports.
    """
    print("[{}] AI Analysis Worker started".format(timezone.now()))
    print("[{}] Scanning for pending reports every 30 seconds...".format(timezone.now()))
    
    while True:
        try:
            # Get reports from last 48 hours with PENDING status
            yesterday = timezone.now() - timedelta(days=2)
            pending_reports = VoluntaryReport.objects.filter(
                ai_analysis_status='PENDING',
                created_at__gte=yesterday
            ).order_by('created_at')

            if pending_reports.exists():
                print("[{}] Found {} pending reports".format(timezone.now(), pending_reports.count()))
                
                # Process one report at a time
                for report in pending_reports:
                    success = run_ai_analysis_for_report(report)
                    if success:
                        print("[{}] Report {} processed successfully".format(timezone.now(), report.id))
                    else:
                        print("[{}] Report {} processing failed".format(timezone.now(), report.id))
                    
                    # Small delay between reports to prevent API rate limiting
                    time.sleep(5)
            else:
                print("[{}] No pending reports found".format(timezone.now()))
            
            # Wait 30 seconds before next scan
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("[{}] Worker stopped by user".format(timezone.now()))
            break
        except Exception as e:
            print("[{}] Worker error: {}".format(timezone.now(), str(e)))
            # Wait before retrying
            time.sleep(60)


if __name__ == "__main__":
    main_worker_loop()
