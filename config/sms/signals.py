from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import voluntary_report, report_analysis

@receiver(post_save, sender=voluntary_report)
def generate_ai_analysis_on_save(sender, instance, created, **kwargs):
    """
    Signal handler to automatically generate AI analysis when voluntary_report is saved
    """
    print(f"Signal triggered: created={created}, instance.pk={instance.pk}")
    
    if created or instance._state.adding:
        # This is a new record, generate AI analysis
        print(f"Generating AI analysis for new report: {instance.description[:50]}...")
        try:
            from .views import test_openai_key
            
            # Create a custom prompt
            prompt = f"""
            Analiza este reporte de seguridad operacional:
            
            Fecha: {instance.date}
            Hora: {instance.time}
            Área: {instance.area}
            Descripción: {instance.description}
            
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
            
            # Call the OpenAI function  
            print("Calling OpenAI API...")
            response = test_openai_key(custom_prompt=prompt)
            print(f"OpenAI response received: {response[:200] if response else 'None'}...")
            
            # Parse the JSON response and create report_analysis record
            import json
            try:
                # Parse the AI response as JSON
                parsed_data = json.loads(response)
                
                # Create the report_analysis record
                # Convert "SI"/"NO" to boolean
                is_valid = parsed_data.get('is_valid', 'NO') == 'SI'
                
                # Create the analysis record
                analysis_record = report_analysis.objects.create(
                    report=instance,
                    is_valid=is_valid,
                    severity=parsed_data.get('severity', ''),
                    probability=parsed_data.get('probability', ''),
                    value=parsed_data.get('value', ''),
                    risk_analysis=parsed_data.get('risk_analysis', ''),
                    recommendations=parsed_data.get('recommendations', '')
                )
                
                print(f"Successfully created report_analysis record: {analysis_record.id}")
                
            except json.JSONDecodeError as e:
                # If JSON parsing fails, print error for debugging
                print(f"JSON parsing error: {str(e)}")
                print(f"Raw response: {response[:200]}...")
                
            except Exception as e:
                # Handle other errors
                print(f"Error creating analysis record: {str(e)}")
            
        except Exception as e:
            error_msg = f"Error generating AI analysis: {str(e)}"
            print(f"Error in signal: {error_msg}")
