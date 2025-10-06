from django.apps import AppConfig


class SchedulerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scheduler'

    def ready(self):
        # Import signal handlers
        try:
            import scheduler.signals  # noqa: F401
        except Exception:
            # Avoid crashing app startup if migrations are running and models aren't ready
            pass