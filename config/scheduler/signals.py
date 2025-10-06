import logging
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.db import transaction
from django.dispatch import receiver

from scheduler.models import FlightRequest
from . import domain_signals

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


@receiver(pre_save, sender=FlightRequest)
def _capture_old_status(sender, instance: FlightRequest, **kwargs):
    """Capture previous status for change detection in post_save."""
    if not instance.pk:
        instance._old_status = None
        return
    try:
        old = FlightRequest.objects.only('status').get(pk=instance.pk)
        instance._old_status = old.status
    except FlightRequest.DoesNotExist:
        instance._old_status = None


@receiver(post_save, sender=FlightRequest)
def notify_student_on_status_change(sender, instance: FlightRequest, created: bool, **kwargs):
    """Email student when request is approved (handled via save)."""
    if created:
        return
    old_status = getattr(instance, '_old_status', None)
    new_status = instance.status
    if old_status == new_status:
        return
    if new_status != 'approved':
        return

    to_email = getattr(instance.student, 'email', None)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    if not to_email or not from_email:
        logger.warning("Student approval email skipped: missing recipient or DEFAULT_FROM_EMAIL")
        return

    def _send():
        fr = (
            FlightRequest.objects.select_related('student', 'slot__aircraft')
            .only('id', 'student__first_name', 'student__last_name', 'student__email', 'slot__date', 'slot__block', 'slot__aircraft__registration')
            .get(pk=instance.pk)
        )
        student_first = fr.student.first_name or ''
        student_last = fr.student.last_name or ''
        aircraft_reg = fr.slot.aircraft.registration if fr.slot and fr.slot.aircraft else 'N/A'
        date_str = fr.slot.date.strftime('%Y-%m-%d') if fr.slot and fr.slot.date else 'N/A'
        block_str = fr.slot.block or 'N/A'

        subject = f"Solicitud de vuelo aprobada – {date_str} {block_str}"
        body = (
            f"Hola {student_first} {student_last},\n\n"
            "Tu solicitud de vuelo ha sido aprobada.\n\n"
            f"Aeronave: {aircraft_reg}\n"
            f"Fecha: {date_str}\n"
            f"Bloque: {block_str}\n"
        )
        try:
            send_mail(subject, body, from_email, [to_email], fail_silently=False)
        except Exception:
            logger.exception("Failed to send student approval email for FlightRequest %s", fr.id)

    transaction.on_commit(_send)


@receiver(domain_signals.flight_request_cancelled)
def notify_student_on_cancelled(sender, instance: FlightRequest, **kwargs):
    """Email student when request is cancelled (custom signal from model)."""
    to_email = getattr(instance.student, 'email', None)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    if not to_email or not from_email:
        logger.warning("Student cancellation email skipped: missing recipient or DEFAULT_FROM_EMAIL")
        return

    def _send():
        try:
            fr = (
                FlightRequest.objects.select_related('student', 'slot__aircraft')
                .only('id', 'student__first_name', 'student__last_name', 'student__email', 'slot__date', 'slot__block', 'slot__aircraft__registration')
                .get(pk=instance.pk)
            )
        except FlightRequest.DoesNotExist:
            # If the object was deleted, best effort with current instance fields
            fr = instance

        student_first = getattr(fr.student, 'first_name', '') or ''
        student_last = getattr(fr.student, 'last_name', '') or ''
        aircraft_reg = getattr(getattr(getattr(fr, 'slot', None), 'aircraft', None), 'registration', None) or 'N/A'
        date_val = getattr(getattr(fr, 'slot', None), 'date', None)
        date_str = date_val.strftime('%Y-%m-%d') if date_val else 'N/A'
        block_str = getattr(getattr(fr, 'slot', None), 'block', None) or 'N/A'

        subject = f"Solicitud de vuelo cancelada – {date_str} {block_str}"
        body = (
            f"Hola {student_first} {student_last},\n\n"
            "Tu solicitud de vuelo ha sido cancelada.\n\n"
            f"Aeronave: {aircraft_reg}\n"
            f"Fecha: {date_str}\n"
            f"Bloque: {block_str}\n"
        )
        try:
            send_mail(subject, body, from_email, [to_email], fail_silently=False)
        except Exception:
            logger.exception("Failed to send student cancellation email for FlightRequest %s", getattr(fr, 'id', 'unknown'))

    transaction.on_commit(_send)


@receiver(domain_signals.instructor_assigned_to_slot)
def notify_instructor_assigned(sender, slot, instructor, **kwargs):
    to_email = getattr(instructor, 'email', None)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    if not to_email or not from_email:
        logger.warning("Instructor assignment email skipped: missing recipient or DEFAULT_FROM_EMAIL")
        return

    def _send():
        aircraft_reg = getattr(getattr(slot, 'aircraft', None), 'registration', None) or 'N/A'
        date_val = getattr(slot, 'date', None)
        date_str = date_val.strftime('%Y-%m-%d') if date_val else 'N/A'
        block_str = getattr(slot, 'block', None) or 'N/A'

        subject = f"Asignado a sesión – {date_str} {block_str}"
        body = (
            f"Hola {getattr(instructor, 'first_name', '') or ''} {getattr(instructor, 'last_name', '') or ''},\n\n"
            "Has sido asignado a una sesión de vuelo.\n\n"
            f"Aeronave: {aircraft_reg}\n"
            f"Fecha: {date_str}\n"
            f"Bloque: {block_str}\n"
        )
        try:
            send_mail(subject, body, from_email, [to_email], fail_silently=False)
        except Exception:
            logger.exception("Failed to send instructor assignment email for slot %s", getattr(slot, 'id', 'unknown'))

    transaction.on_commit(_send)


@receiver(domain_signals.instructor_removed_from_slot)
def notify_instructor_removed(sender, slot, instructor, **kwargs):
    to_email = getattr(instructor, 'email', None)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    if not to_email or not from_email:
        logger.warning("Instructor removal email skipped: missing recipient or DEFAULT_FROM_EMAIL")
        return

    def _send():
        aircraft_reg = getattr(getattr(slot, 'aircraft', None), 'registration', None) or 'N/A'
        date_val = getattr(slot, 'date', None)
        date_str = date_val.strftime('%Y-%m-%d') if date_val else 'N/A'
        block_str = getattr(slot, 'block', None) or 'N/A'

        subject = f"Removido de sesión – {date_str} {block_str}"
        body = (
            f"Hola {getattr(instructor, 'first_name', '') or ''} {getattr(instructor, 'last_name', '') or ''},\n\n"
            "Has sido removido de una sesión de vuelo.\n\n"
            f"Aeronave: {aircraft_reg}\n"
            f"Fecha: {date_str}\n"
            f"Bloque: {block_str}\n"
        )
        try:
            send_mail(subject, body, from_email, [to_email], fail_silently=False)
        except Exception:
            logger.exception("Failed to send instructor removal email for slot %s", getattr(slot, 'id', 'unknown'))

    transaction.on_commit(_send)


