from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.conf import settings
from .models import VoluntaryHazardReport
import logging

logger = logging.getLogger('sms.signals')

SMS_NOTIFICATION_SUBJECT = "Nuevo análisis de Reporte Voluntario de Peligro"
SMS_NOTIFICATION_MESSAGE = """
Buen día,

He completado el análisis de un nuevo Reporte Voluntario de Peligro.

Fecha: {report_date}
Hora: {report_time}
Área: {report_area}
Descripción: {report_description}

Para ver el análisis de riesgos y acciones de mitigación, por favor acceda al sistema SARA.

Atentamente,
SARA
(Safety Analyst and Reporting Assistant)
"""

@receiver(post_save, sender=VoluntaryHazardReport)
def send_rvp_analysis_email(instance, created, **kwargs):
    """
    Send an email notification when the RVP AI analysis is completed.
    """
    if created or instance.ai_analysis_status != 'COMPLETED':
        return

    # Recipients list
    recipients = [
        r for r in [
            settings.SMS_NOTIFICATION_EMAIL_1,
            settings.SMS_NOTIFICATION_EMAIL_2,
            settings.SMS_NOTIFICATION_EMAIL_3,
            settings.SMS_NOTIFICATION_EMAIL_4,
        ] if r
    ]

    try:
        message_body = SMS_NOTIFICATION_MESSAGE.format(
            report_date=instance.date.strftime('%d/%m/%Y'),
            report_time=instance.time.strftime('%H:%M'),
            report_area=instance.get_area_display(),
            report_description=instance.description
        )

        email = EmailMessage(
            subject=SMS_NOTIFICATION_SUBJECT,
            body=message_body,
            from_email=settings.EMAIL_HOST_USER,
            to=recipients
        )
        email.send(fail_silently=False)
        logger.info(f"RVP analysis email sent to recipients: {recipients}")
    except Exception as e:
        logger.error(f"Failed to send RVP analysis email to recipients: {recipients}. Error: {e}")