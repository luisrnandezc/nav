import os
import sys
import django
from django.utils.timezone import localdate

project_dir = os.path.dirname(os.path.abspath(__file__))
django_dir = os.path.join(project_dir, '..', '..')
sys.path.insert(0, django_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from scheduler.models import FlightRequest

def cancel_overdue_requests():
    today = localdate()
    overdue = FlightRequest.objects.filter(
        status='pending',
        slot__date__lt=today
    ).select_related('slot')
    
    for request in overdue:
        request.cancel()
        print(f"Cancelled request {request.id}")

if __name__ == "__main__":
    cancel_overdue_requests()