from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import VoluntaryReport, ReportAnalysis
from django.core.mail import EmailMessage, get_connection
from django.conf import settings
import logging

logger = logging.getLogger('sms.signals')

SMS_NOTIFICATION_SUBJECT_1 = "Nuevo análisis de reporte voluntario de SMS - Director"
SMS_NOTIFICATION_SUBJECT_2 = "Nuevo análisis de reporte voluntario de SMS - Gerente SMS"

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

@receiver(post_save, sender=ReportAnalysis)
def send_sms_analysis_email(sender, instance, created, **kwargs):
    if not created:
        return

    # List of recipients
    recipients = [
        {
            "email": settings.SMS_NOTIFICATION_EMAIL_1,
            "subject": SMS_NOTIFICATION_SUBJECT_1,
            "message": SMS_NOTIFICATION_MESSAGE_1,
            "name": "Elías"
        },
        {
            "email": settings.SMS_NOTIFICATION_EMAIL_2,
            "subject": SMS_NOTIFICATION_SUBJECT_2,
            "message": SMS_NOTIFICATION_MESSAGE_2,
            "name": "Cap. Raúl"
        }
    ]

    # Open a single SMTP connection
    connection = get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        username=settings.EMAIL_HOST_USER,
        password=settings.EMAIL_HOST_PASSWORD,
        use_tls=settings.EMAIL_USE_TLS,
        fail_silently=False
    )

    sent_count = 0
    failed_count = 0

    for recipient in recipients:
        try:
            if not recipient["email"]:
                logger.error(f"Email address not configured for {recipient['name']}")
                failed_count += 1
                continue

            message_body = recipient["message"].format(
                severity=instance.severity,
                probability=instance.probability,
                value=instance.value,
                risk_analysis=instance.risk_analysis
            )

            email = EmailMessage(
                subject=recipient["subject"],
                body=message_body,
                from_email=settings.EMAIL_HOST_USER,  # Always your Gmail
                to=[recipient["email"]],
                connection=connection
            )
            email.send()
            logger.info(f"Email sent to {recipient['name']} ({recipient['email']})")
            sent_count += 1

        except Exception as e:
            logger.error(f"Failed to send email to {recipient['name']} ({recipient['email']}): {e}")
            failed_count += 1

    logger.info(f"Email sending summary: {sent_count} sent, {failed_count} failed")
