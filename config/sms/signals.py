from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import VoluntaryReport, ReportAnalysis
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger('sms.signals')

SMS_NOTIFICATION_SUBJECT_1 = """Nuevo análisis de reporte voluntario de SMS - Director"""
SMS_NOTIFICATION_SUBJECT_2 = """Nuevo análisis de reporte voluntario de SMS - Gerente SMS"""

SMS_NOTIFICATION_MESSAGE_1 = """
Buen día Elías. He completado el análisis de un nuevo reporte voluntario de SMS.

Severidad: {severity}
Probabilidad: {probability}
Valor alfanumérico: {value}
Riesgo: {risk_analysis}

Atentamente,
SARA.
"""
SMS_NOTIFICATION_MESSAGE_2 = """
Buen día Cap. Raúl. He completado el análisis de un nuevo reporte voluntario de SMS.

Severidad: {severity}
Probabilidad: {probability}
Valor alfanumérico: {value}
Riesgo: {risk_analysis}

Atentamente,
SARA.
"""


@receiver(post_save, sender=VoluntaryReport)
def set_ai_analysis_pending(sender, instance, created, **kwargs):
    """
    Signal handler to set AI analysis status to PENDING when voluntary_report is saved.
    The always-on task worker will pick up pending reports for processing.
    """
    if created and not instance._state.adding:
        # This is a new record that was just saved
        try:
            # Set status to PENDING - worker will process it
            VoluntaryReport.objects.filter(id=instance.id).update(ai_analysis_status='PENDING')
        except Exception as e:
            # If we can't set status, leave it as default
            pass

@receiver(post_save, sender=ReportAnalysis)
def send_sms_analysis_email(sender, instance, created, **kwargs):
    """
    Signal handler to send SMS analysis email when report_analysis is saved.
    """
    if created:
        # DEBUG: Log the configuration being used
        print(f"=== EMAIL CONFIGURATION DEBUG ===")
        print(f"ON_PYTHONANYWHERE: {getattr(settings, 'ON_PYTHONANYWHERE', 'NOT SET')}")
        print(f"DEBUG: {getattr(settings, 'DEBUG', 'NOT SET')}")
        print(f"SMS_NOTIFICATION_EMAIL_1: {settings.SMS_NOTIFICATION_EMAIL_1}")
        print(f"SMS_NOTIFICATION_EMAIL_2: {settings.SMS_NOTIFICATION_EMAIL_2}")
        print(f"================================")
        
        # Define the recipients of the email
        recipients = [
            {
                'email': settings.SMS_NOTIFICATION_EMAIL_1,
                'subject': SMS_NOTIFICATION_SUBJECT_1,
                'message': SMS_NOTIFICATION_MESSAGE_1,
                'name': 'Elías'
            },
            {
                'email': settings.SMS_NOTIFICATION_EMAIL_2,
                'subject': SMS_NOTIFICATION_SUBJECT_2,
                'message': SMS_NOTIFICATION_MESSAGE_2,
                'name': 'Cap. Raúl'
            }
        ]

        # Track results
        sent_count = 0
        failed_count = 0

        for recipient in recipients:
            try:
                # Validate email address
                if not recipient['email']:
                    logger.error(f"Email address is not configured for {recipient['name']}")
                    failed_count += 1
                    continue

                # Format the message
                message = recipient['message'].format(
                    severity=instance.severity,
                    probability=instance.probability,
                    value=instance.value,
                    risk_analysis=instance.risk_analysis,
                )

                # Send email
                send_mail(
                    recipient['subject'],
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient['email']],
                    fail_silently=False,
                )
                logger.info(f"Email sent to {recipient['name']} {recipient['email']} with subject 'Nuevo análisis de reporte voluntario de SMS'")
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send SMS analysis email to {recipient['name']} {recipient['email']}: {e}")
                failed_count += 1
        
        # Summary log
        logger.info(f"Email sent to {sent_count} recipients out of {len(recipients)} recipients")
        logger.info(f"Email failed to send to {failed_count} recipients out of {len(recipients)} recipients")