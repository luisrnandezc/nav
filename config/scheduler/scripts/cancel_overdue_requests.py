import os
import sys
import django
from django.utils.timezone import localdate

project_dir = os.path.dirname(os.path.abspath(__file__))
django_dir = os.path.join(project_dir, '..', '..')
sys.path.insert(0, django_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from scheduler.models import FlightRequest, FlightSlot

def cancel_overdue_requests(today):
    overdue = FlightRequest.objects.filter(
        status='pending',
        slot__date__lt=today
    ).select_related('slot')
    
    for request in overdue:
        request.cancel()
        print(f"Cancelled request {request.id}")

def cancel_overdue_slots(today):
    overdue = FlightSlot.objects.filter(
        status__in=['available', 'pending', 'reserved'],
        date__lt=today
    )
    
    for slot in overdue:
        slot.status='unavailable'
        slot.save()
        print(f"Marked slot as unavailable {slot.id}")


if __name__ == "__main__":
    today = localdate()
    cancel_overdue_requests(today)
    cancel_overdue_slots(today)