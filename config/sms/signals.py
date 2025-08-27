from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ReportAnalysis
from django.core.mail import EmailMessage
from django.conf import settings
import logging

logger = logging.getLogger('sms.signals')

SMS_NOTIFICATION_SUBJECT = "Nuevo análisis de reporte voluntario de SMS"
SMS_NOTIFICATION_MESSAGE = """
Buen día,

He completado el análisis de un nuevo reporte voluntario de SMS.

Severidad: {severity}

Probabilidad: {probability}

Valor alfanumérico: {value}

Análisis de riesgo: {risk_analysis}

Recomendaciones: {recommendations}

Atentamente,
SARA
(Safety Analyst and Reporting Assistant)
"""

@receiver(post_save, sender=ReportAnalysis)
def send_sms_analysis_email(sender, instance, created, **kwargs):
    if not created:
        return

    # Recipients list
    recipients = [
        settings.SMS_NOTIFICATION_EMAIL_1,
        settings.SMS_NOTIFICATION_EMAIL_2,
        settings.SMS_NOTIFICATION_EMAIL_3,
    ]

    try:
        message_body = SMS_NOTIFICATION_MESSAGE.format(
            severity=instance.severity,
            probability=instance.probability,
            value=instance.value,
            risk_analysis=instance.risk_analysis,
            recommendations=instance.recommendations
        )

        email = EmailMessage(
            subject=SMS_NOTIFICATION_SUBJECT,
            body=message_body,
            from_email=settings.EMAIL_HOST_USER,
            to=recipients
        )
        email.send(fail_silently=False)
        logger.info(f"Email sent to all recipients: {recipients}")
    except Exception as e:
        logger.error(f"Failed to send SMS analysis email: {e}")