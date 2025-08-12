from django.apps import AppConfig


class SmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sms'
    verbose_name = 'Safety Management System'
    
    def ready(self):
        import sms.signals  # Import signals when app is ready
