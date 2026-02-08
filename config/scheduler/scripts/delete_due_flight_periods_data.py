"""
Clean up past flight scheduling data.

Tasks:
1. Delete flight periods whose end_date is before today (end_date < today).
   Periods with end_date == today are kept. CASCADE deletes their slots and requests.

2. Delete all flight requests whose slot date is before today, and mark those
   slots as unavailable.

3. Mark any remaining past-dated slots (no request) as unavailable.
"""
import os
import sys
import django
from django.utils.timezone import localdate
from django.db import transaction

project_dir = os.path.dirname(os.path.abspath(__file__))
django_dir = os.path.join(project_dir, '..', '..')
sys.path.insert(0, django_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from scheduler.models import FlightRequest, FlightSlot, FlightPeriod


def delete_past_flight_periods(today):
    """
    Delete all flight periods for which end_date < today.
    If end_date is today, the period is kept. If end_date was yesterday or earlier, delete.
    CASCADE removes all slots and flight requests for those periods.
    """
    past_periods = FlightPeriod.objects.filter(end_date__lt=today)
    count = past_periods.count()
    past_periods.delete()
    if count:
        print(f"Deleted {count} flight period(s) with end_date before {today}.")
    return count


def delete_past_flight_requests_and_mark_slots_unavailable(today):
    """
    Delete all flight requests whose slot date is before today.
    Mark each affected slot as unavailable (past slots are not bookable).
    """
    past_requests = FlightRequest.objects.filter(slot__date__lt=today).select_related('slot')
    slot_ids_to_mark_unavailable = []
    deleted = 0
    for request in past_requests:
        slot_ids_to_mark_unavailable.append(request.slot_id)
        req_id, slot_date = request.id, request.slot.date
        request.delete()
        deleted += 1
        print(f"Deleted flight request {req_id} (slot date: {slot_date})")
    if slot_ids_to_mark_unavailable:
        updated = FlightSlot.objects.filter(pk__in=slot_ids_to_mark_unavailable).update(
            status='unavailable', student=None, instructor=None, aircraft=None
        )
        print(f"Marked {updated} slot(s) as unavailable.")
    if deleted:
        print(f"Deleted {deleted} flight request(s) with slot date before {today}.")
    return deleted


def mark_past_dated_slots_as_unavailable(today):
    """
    Mark slots with date < today as unavailable if they are still available/pending/reserved.
    (Slots belonging to deleted periods are already gone; this covers slots from periods
    that are still active but have past dates.)
    """
    overdue = FlightSlot.objects.filter(
        status__in=['available', 'pending', 'reserved'],
        date__lt=today
    )
    for slot in overdue:
        slot.status = 'unavailable'
        slot.student = None
        slot.save()
        print(f"Marked slot as unavailable {slot.id}")


def run_all(today=None):
    if today is None:
        today = localdate()
    with transaction.atomic():
        # 1) Delete past flight periods (and their slots/requests via CASCADE)
        delete_past_flight_periods(today)
        # 2) Delete any remaining past-dated flight requests and mark slots unavailable
        delete_past_flight_requests_and_mark_slots_unavailable(today)
        # 3) Mark any remaining past-dated slots as unavailable (e.g. no request but slot exists)
        mark_past_dated_slots_as_unavailable(today)
    print("Done.")


if __name__ == "__main__":
    today = localdate()
    run_all(today)
