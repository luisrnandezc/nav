from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StudentPayment
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger('payments.signals')

PAYMENT_NOTIFICATION_SUBJECT = """Nuevo pago agregado"""
PAYMENT_NOTIFICATION_MESSAGE = """
Se ha agregado un nuevo pago de ${amount} a la cuenta de {student_name}.
Tipo de pago: {payment_type}
Fecha de pago: {date_added}
Estado: Pendiente de confirmación
"""

@receiver(post_save, sender=StudentPayment)
def send_payment_confirmation_email(sender, instance, created, **kwargs):
    """
    Signal handler to send payment confirmation email when payment is saved.
    """
    if created and instance.confirmed is False:
        try:
            # Send email to the school director
            send_mail(
                PAYMENT_NOTIFICATION_SUBJECT,
                PAYMENT_NOTIFICATION_MESSAGE.format(
                    amount=instance.amount,
                    payment_type=instance.type,
                    student_name=instance.student_profile.user.get_full_name(),
                    date_added=instance.date_added,
                ),
                settings.DEFAULT_FROM_EMAIL,
                [settings.PAYMENTS_NOTIFICATION_EMAIL],
                fail_silently=False,
            )
            logger.info(f"Email sent to {settings.PAYMENTS_NOTIFICATION_EMAIL} with subject 'Nuevo pago agregado'")
        except Exception as e:
            logger.error(f"Failed to send payment confirmation email to {settings.PAYMENTS_NOTIFICATION_EMAIL}: {e}")
