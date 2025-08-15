from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import voluntary_report

@receiver(post_save, sender=voluntary_report)
def schedule_ai_analysis_on_save(sender, instance, created, **kwargs):
    """
    Signal handler to schedule AI analysis when voluntary_report is saved
    The actual AI analysis will be handled by the always-on worker
    """
    print(f"Signal triggered: created={created}, instance.pk={instance.pk}")
    
    if created or instance._state.adding:
        # This is a new record, set status to PENDING for the worker to process
        print(f"New report {instance.id} saved. Status set to PENDING for AI analysis.")
        
        # The status is already set to 'PENDING' by default in the model
        # The always-on worker will pick this up and process it
        
        print(f"Report {instance.id} queued for AI analysis. Worker will process it automatically.")
