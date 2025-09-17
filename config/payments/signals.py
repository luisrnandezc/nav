from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StudentTransaction
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger('payments.signals')

TRANSACTION_NOTIFICATION_SUBJECT = """Nueva transacción agregada"""
TRANSACTION_NOTIFICATION_MESSAGE = """
Se ha agregado una nueva transacción de ${amount} a la cuenta de {student_name}.
Tipo de transacción: {transaction_type}
Fecha de transacción: {date_added}
Estado: Pendiente de confirmación
"""

@receiver(post_save, sender=StudentTransaction)
def send_transaction_confirmation_email(sender, instance, created, **kwargs):
    """
    Signal handler to send transaction confirmation email when transaction is saved.
    """
    if created and instance.confirmed is False:
        try:
            # Send email to the school director
            send_mail(
                TRANSACTION_NOTIFICATION_SUBJECT,
                TRANSACTION_NOTIFICATION_MESSAGE.format(
                    amount=instance.amount,
                    transaction_type=instance.type,
                    student_name=instance.student_profile.user.get_full_name(),
                    date_added=instance.date_added,
                ),
                settings.DEFAULT_FROM_EMAIL,
                [settings.TRANSACTIONS_NOTIFICATION_EMAIL],
                fail_silently=False,
            )
            logger.info(f"Email sent to {settings.TRANSACTIONS_NOTIFICATION_EMAIL} with subject 'Nueva transacción agregada'")
        except Exception as e:
            logger.error(f"Failed to send transaction confirmation email to {settings.TRANSACTIONS_NOTIFICATION_EMAIL}: {e}")
