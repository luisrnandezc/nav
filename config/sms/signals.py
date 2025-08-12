from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import voluntary_report

@receiver(post_save, sender=voluntary_report)
def generate_ai_analysis_on_save(sender, instance, created, **kwargs):
    """
    Signal handler to automatically generate AI analysis when voluntary_report is saved
    """
    if created or instance._state.adding:
        # This is a new record, generate AI analysis
        try:
            from .views import test_openai_key
            
            # Create a custom prompt
            prompt = f"""
            Analiza este reporte voluntario y proporciona recomendaciones:
            
            Fecha: {instance.date}
            Hora: {instance.time}
            Área: {instance.area}
            Descripción: {instance.description}
            
            Por favor, proporciona:
            1. Evaluación de riesgos
            2. Causas potenciales
            3. Medidas preventivas recomendadas
            4. Mejoras de seguridad
            """
            
            # Call the OpenAI function
            response = test_openai_key(custom_prompt=prompt)
            
            # Update the ai_analysis field without triggering the signal again
            voluntary_report.objects.filter(pk=instance.pk).update(ai_analysis=response)
            
        except Exception as e:
            error_msg = f"Error generating AI analysis: {str(e)}"
            # Update with error message
            voluntary_report.objects.filter(pk=instance.pk).update(ai_analysis=error_msg)
