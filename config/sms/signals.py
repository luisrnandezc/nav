from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.conf import settings
from .models import VoluntaryHazardReport, MitigationAction, Risk
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
def send_vhr_analysis_email(instance, created, **kwargs):
    """
    Send an email notification when the VHR AI analysis is completed.
    Only sends email once per report when status becomes 'COMPLETED'.
    """
    # Don't send on creation or if status is not COMPLETED
    if created or instance.ai_analysis_status != 'COMPLETED':
        return
    
    # Don't send if email was already sent
    if instance.analysis_email_sent:
        return
    
    # Check if ai_analysis_status was actually updated in this save
    update_fields = kwargs.get('update_fields')
    if update_fields and 'ai_analysis_status' not in update_fields:
        # Status wasn't changed in this save, so don't send email
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
        
        # Mark email as sent to prevent duplicate emails
        instance.analysis_email_sent = True
        instance.save(update_fields=['analysis_email_sent'])
        
        logger.info(f"VHR analysis email sent to recipients: {recipients}")
    except Exception as e:
        logger.error(f"Failed to send VHR analysis email to recipients: {recipients}. Error: {e}")


def check_and_update_report_resolved_status(report):
    """
    Helper function to check if all risks are mitigated and update report.is_resolved.
    """
    # Get all risks for this report
    all_risks = report.risks.all()
    
    # Check if there are any risks at all
    if not all_risks.exists():
        # No risks means report cannot be resolved
        if report.is_resolved:
            report.is_resolved = False
            report.save(update_fields=['is_resolved'])
        return
    
    # Check if all risks are MITIGATED
    all_mitigated = all(risk.condition == 'MITIGATED' for risk in all_risks)
    
    # Update is_resolved field
    if all_mitigated:
        if not report.is_resolved:
            report.is_resolved = True
            report.save(update_fields=['is_resolved'])
            logger.info(f"Report {report.id} marked as resolved - all risks mitigated")
    else:
        # If not all risks are mitigated, make sure is_resolved is False
        if report.is_resolved:
            report.is_resolved = False
            report.save(update_fields=['is_resolved'])
            logger.info(f"Report {report.id} marked as unresolved - not all risks mitigated")


@receiver(post_save, sender=MitigationAction)
def update_report_resolved_status_on_mmr_change(instance, created, **kwargs):
    """
    Update the report's is_resolved field when MMR status changes.
    This triggers a check to see if all risks are now mitigated.
    """
    # Only check if status field was updated (to avoid unnecessary queries)
    update_fields = kwargs.get('update_fields')
    if update_fields and 'status' not in update_fields:
        return
    
    # Get the report through the risk
    report = instance.risk.report
    
    # Check and update resolved status
    check_and_update_report_resolved_status(report)


@receiver(post_save, sender=Risk)
def update_report_resolved_status_on_risk_change(instance, created, **kwargs):
    """
    Update the report's is_resolved field when risk condition changes.
    Sets is_resolved=True when all risks for a report are MITIGATED.
    """
    # Only check if condition field was updated (to avoid unnecessary queries)
    update_fields = kwargs.get('update_fields')
    if update_fields and 'condition' not in update_fields:
        return
    
    # Get the report
    report = instance.report
    
    # Check and update resolved status
    check_and_update_report_resolved_status(report)