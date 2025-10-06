import logging
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.db import transaction
from django.dispatch import receiver

from scheduler.models import FlightRequest

logger = logging.getLogger(__name__)


@receiver(post_save, sender=FlightRequest)
def notify_staff_on_flight_request_created(sender, instance: FlightRequest, created: bool, **kwargs):
    """Send an email to staff when a student submits a new flight request."""
    if not created:
        return

    staff_email = getattr(settings, 'OPS_NOTIFICATION_EMAIL', None)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    if not staff_email or not from_email:
        logger.warning(
            "Email notification skipped: missing OPS_NOTIFICATION_EMAIL or DEFAULT_FROM_EMAIL"
        )
        return

    # Defer sending until the transaction successfully commits
    def _send():
        # Re-fetch with related fields to avoid lazy access after commit
        fr = (
            FlightRequest.objects.select_related('student', 'slot__aircraft')
            .only('id', 'student__first_name', 'student__last_name', 'slot__date', 'slot__block', 'slot__aircraft__registration')
            .get(pk=instance.pk)
        )

        student_first = fr.student.first_name or ''
        student_last = fr.student.last_name or ''
        aircraft_reg = fr.slot.aircraft.registration if fr.slot and fr.slot.aircraft else 'N/A'
        date_str = fr.slot.date.strftime('%Y-%m-%d') if fr.slot and fr.slot.date else 'N/A'
        block_str = fr.slot.block or 'N/A'

        subject = f"Nueva solicitud de vuelo – {student_first} {student_last} – {date_str} {block_str}"
        body = (
            "Se recibió una nueva solicitud de vuelo.\n\n"
            f"Estudiante: {student_first} {student_last}\n"
            f"Aeronave: {aircraft_reg}\n"
            f"Fecha: {date_str}\n"
            f"Bloque: {block_str}\n"
        )

        try:
            # fail_silently=False so we can capture and log failures
            send_mail(subject, body, from_email, [staff_email], fail_silently=False)
        except Exception as exc:
            logger.exception("Failed to send staff notification email for FlightRequest %s", fr.id)

    transaction.on_commit(_send)


