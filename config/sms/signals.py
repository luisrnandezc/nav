from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.conf import settings
import logging
import json

logger = logging.getLogger('sms.signals')

SMS_NOTIFICATION_SUBJECT = "Nuevo análisis de reporte de peligro voluntario de SMS"
SMS_NOTIFICATION_MESSAGE = """
Buen día,

He completado el análisis de un nuevo reporte voluntario de SMS.

Severidad: {severity}

Probabilidad: {probability}

Valor alfanumérico: {value}

Para ver el análisis completo de riesgos y recomendaciones, por favor acceda al sistema SMS.

Atentamente,
SARA
(Safety Analyst and Reporting Assistant)
"""

@receiver(post_save)
def send_sms_analysis_email(instance, created, **kwargs):
    if not created:
        return

    # Recipients list
    recipients = [
        settings.SMS_NOTIFICATION_EMAIL_1,
        settings.SMS_NOTIFICATION_EMAIL_2,
        settings.SMS_NOTIFICATION_EMAIL_3,
        settings.SMS_NOTIFICATION_EMAIL_4,
    ]

    try:
        message_body = SMS_NOTIFICATION_MESSAGE.format(
            severity=instance.severity,
            probability=instance.probability,
            value=instance.value
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