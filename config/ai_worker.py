#!/usr/bin/env python
"""
AI Analysis Worker - Simple Always-On Task for PythonAnywhere
This script runs continuously and processes pending SMS reports for AI analysis.
"""

import os
import django
import time
import json
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from sms.models import voluntary_report, report_analysis
from sms.views import test_openai_key

def process_ai_analysis(report):
    """
    Process AI analysis for a single report
    """
    try:
        print(f"[{datetime.now()}] Processing AI analysis for report {report.id}: {report.description[:50]}...")
        
        # Update status to PROCESSING
        report.ai_analysis_status = 'PROCESSING'
        report.save(update_fields=['ai_analysis_status'])
        
        # Create the AI prompt
        prompt = f"""
        Analiza este reporte de seguridad operacional:
        
        Fecha: {report.date}
        Hora: {report.time}
        Área: {report.area}
        Descripción: {report.description}
        
        Por favor, ejecuta las siguientes tareas:

        1. Analiza el reporte y determina si es un reporte de seguridad válido, es decir, que el contenido del reporte contiene
        información de una condición, situación o suceso relacionado con la seguridad operacional. Debes ser muy estricto con este criterio, por
        ejemplo, si el reporte es sobre un problema con uno de las pizarras electrónicas usadas para dar clases, no es un reporte de seguridad válido.

        2. Si es un reporte de seguridad válido, asígnale un Nivel de Severidad y un Nivel de Probabilidad de acuerdo a la siguiente escala:
            2.1 Nivel de severidad: insignificante (E), marginal (D), significativo (C), crítico (B) y catastrófico (A).
            2.2 Nivel de probabilidad: improbable (1), remoto (2), probable (3), ocasional (4) y frecuente (5).

            Une los valores de Severidad y Probabilidad para obtener un valor alfanumérico.

            Ejemplo: un reporte calificado como "crítico (C)" y "ocasional (4)" tiene un valor de "C4".
            Ejemplo: un reporte calificado como "marginal (D)" y "probable (3)" tiene un valor de "D3".

            2.3 Si el reporte no es válido, asigna un valor numérico de "0".

        3. Ejecuta un análisis de riesgos del reporte, considerando el valor alfanumérico asignado en el punto 2.

        4. Genera recomendaciones para mejorar la seguridad operacional, considerando el análisis de riesgos y el valor alfanumérico asignado en el punto 2.

        5. IMPORTANTE: Responde ÚNICAMENTE con un JSON válido. NO incluyas texto explicativo antes o después del JSON.
        
        El JSON debe tener exactamente esta estructura:
        {{
            "is_valid": "SI",
            "severity": "C",
            "probability": "3", 
            "value": "C3",
            "risk_analysis": "Análisis detallado de riesgos del reporte",
            "recommendations": "Recomendaciones específicas para mejorar la seguridad operacional"
        }}
        
        NOTA: Reemplaza los valores de ejemplo con los valores reales para este reporte específico.
        """
        
        # Call OpenAI API
        print(f"[{datetime.now()}] Calling OpenAI API for report {report.id}...")
        response = test_openai_key(custom_prompt=prompt)
        
        if not response or response.startswith("Error:"):
            raise Exception(f"OpenAI API error: {response}")
        
        # Parse JSON response
        try:
            parsed_data = json.loads(response)
        except json.JSONDecodeError as e:
            raise Exception(f"JSON parsing error: {str(e)}. Response: {response[:200]}")
        
        # Create analysis record
        is_valid = parsed_data.get('is_valid', 'NO') == 'SI'
        
        analysis_record = report_analysis.objects.create(
            report=report,
            is_valid=is_valid,
            severity=parsed_data.get('severity', ''),
            probability=parsed_data.get('probability', ''),
            value=parsed_data.get('value', ''),
            risk_analysis=parsed_data.get('risk_analysis', ''),
            recommendations=parsed_data.get('recommendations', '')
        )
        
        # Update status to COMPLETED
        report.ai_analysis_status = 'COMPLETED'
        report.save(update_fields=['ai_analysis_status'])
        
        print(f"[{datetime.now()}] Successfully completed AI analysis for report {report.id}")
        return True
        
    except Exception as e:
        error_msg = f"Error processing report {report.id}: {str(e)}"
        print(f"[{datetime.now()}] {error_msg}")
        
        # Update status to FAILED
        try:
            report.ai_analysis_status = 'FAILED'
            report.save(update_fields=['ai_analysis_status'])
        except:
            pass
        
        return False

def main_worker_loop():
    """
    Main worker loop that runs continuously
    """
    print(f"[{datetime.now()}] AI Analysis Worker started. Monitoring for pending reports...")
    
    while True:
        try:
            # Get all reports waiting for AI analysis
            pending_reports = voluntary_report.objects.filter(
                ai_analysis_status='PENDING'
            ).order_by('created_at')  # Process oldest first
            
            if pending_reports.exists():
                print(f"[{datetime.now()}] Found {pending_reports.count()} pending reports")
                
                for report in pending_reports:
                    try:
                        success = process_ai_analysis(report)
                        if success:
                            print(f"[{datetime.now()}] Report {report.id} processed successfully")
                        else:
                            print(f"[{datetime.now()}] Report {report.id} failed to process")
                        
                        # Small delay between reports to avoid overwhelming the API
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"[{datetime.now()}] Unexpected error processing report {report.id}: {str(e)}")
                        continue
            else:
                print(f"[{datetime.now()}] No pending reports. Waiting...")
            
            # Wait before checking again
            time.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            print(f"[{datetime.now()}] Error in main worker loop: {str(e)}")
            time.sleep(30)  # Wait longer on error before retrying
            continue

if __name__ == "__main__":
    try:
        main_worker_loop()
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Worker stopped by user")
    except Exception as e:
        print(f"\n[{datetime.now()}] Fatal error: {str(e)}")
        exit(1)
