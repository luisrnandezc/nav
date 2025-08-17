from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import voluntary_report

@receiver(post_save, sender=voluntary_report)
def set_ai_analysis_pending(sender, instance, created, **kwargs):
    """
    Signal handler to set AI analysis status to PENDING when voluntary_report is saved.
    The always-on task worker will pick up pending reports for processing.
    """
    if created and not instance._state.adding:
        # This is a new record that was just saved
        try:
            # Set status to PENDING - worker will process it
            voluntary_report.objects.filter(id=instance.id).update(ai_analysis_status='PENDING')
        except Exception as e:
            # If we can't set status, leave it as default
            pass
