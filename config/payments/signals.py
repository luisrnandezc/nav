from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StudentPayment
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=StudentPayment)
def send_payment_confirmation_email(sender, instance, created, **kwargs):
    """
    Signal handler to send payment confirmation email when payment is saved.
    """
    if created and instance.confirmed is False:
        # Send email to student
        send_mail(
            'Nuevo pago agregado',
            f'Se ha agregado un nuevo pago de ${instance.amount} a la cuenta de {instance.student_profile.user.username}.',
            settings.EMAIL_HOST_USER,
            [settings.RECEIVER_EMAIL],
            fail_silently=False,
        )
