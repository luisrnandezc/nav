"""
Tests for the cancel_overdue_requests script.

Verifies that:
1. Flight periods with end_date < today are deleted (with their slots and requests).
2. Flight requests with slot date < today are deleted and their slots marked unavailable.
3. Remaining past-dated slots are marked unavailable.
4. After the script runs, reservation logic and balance limits are unchanged (students
   with balance < 500 cannot create requests unless they have credit; balance >= 500
   allows balance // 500 requests).
"""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from scheduler.models import FlightPeriod, FlightSlot, FlightRequest
from scheduler.scripts.cancel_overdue_requests import run_all
from .factories import (
    AircraftFactory,
    UserFactory,
    StudentProfileFactory,
    FlightPeriodFactory,
    FlightRequestFactory,
)


def localdate():
    return timezone.localdate()


class CancelOverdueRequestsScriptTest(TestCase):
    """Test the cancel_overdue_requests script cleanup and its impact on reservation logic."""

    def setUp(self):
        self.today = localdate()
        self.aircraft_a = AircraftFactory()
        self.aircraft_b = AircraftFactory()

        # Period A: entirely in the past (end_date < today) — will be deleted
        self.period_a_start = self.today - timedelta(days=14)
        self.period_a_end = self.today - timedelta(days=8)  # 7-day period
        self.period_a = FlightPeriodFactory(
            aircraft=self.aircraft_a,
            start_date=self.period_a_start,
            end_date=self.period_a_end,
            is_active=False,
        )
        self.period_a.generate_slots()
        self.slot_a = FlightSlot.objects.filter(flight_period=self.period_a).first()

        # Period B: past start, future end (end_date >= today) — kept
        self.period_b_start = self.today - timedelta(days=7)
        self.period_b_end = self.today + timedelta(days=6)  # 14-day period
        self.period_b = FlightPeriodFactory(
            aircraft=self.aircraft_b,
            start_date=self.period_b_start,
            end_date=self.period_b_end,
            is_active=True,
        )
        self.period_b.generate_slots()
        slots_b = list(FlightSlot.objects.filter(flight_period=self.period_b).order_by('date'))
        self.slot_b_past = next(s for s in slots_b if s.date < self.today)
        self.slot_b_future = next(s for s in slots_b if s.date >= self.today)

        # One student to hold the pre-cleanup requests (so test students have 0 after cleanup)
        self.dummy_student = UserFactory()
        StudentProfileFactory(user=self.dummy_student, balance=2000.00)

        self.fr_a = FlightRequestFactory(
            student=self.dummy_student,
            slot=self.slot_a,
            status='pending',
        )
        self.fr_b_past = FlightRequestFactory(
            student=self.dummy_student,
            slot=self.slot_b_past,
            status='pending',
        )
        self.fr_b_future = FlightRequestFactory(
            student=self.dummy_student,
            slot=self.slot_b_future,
            status='approved',
        )
        self.slot_b_future.status = 'reserved'
        self.slot_b_future.student = self.dummy_student
        self.slot_b_future.save()

        # Three students for post-cleanup reservation limit checks
        self.student_low = UserFactory()
        StudentProfileFactory(user=self.student_low, balance=400.00, has_credit=False)

        self.student_high = UserFactory()
        StudentProfileFactory(user=self.student_high, balance=1000.00, has_credit=False)

        self.student_credit = UserFactory()
        StudentProfileFactory(user=self.student_credit, balance=400.00, has_credit=True)

    def test_script_deletes_past_period_and_keeps_spanning_period(self):
        """Period A (end_date < today) is deleted; period B (end_date >= today) is kept."""
        period_a_id = self.period_a.id
        period_b_id = self.period_b.id
        run_all(today=self.today)
        self.assertFalse(FlightPeriod.objects.filter(pk=period_a_id).exists())
        self.assertTrue(FlightPeriod.objects.filter(pk=period_b_id).exists())

    def test_script_deletes_past_requests_and_keeps_future_request(self):
        """Request for period A is gone (CASCADE). Request for past slot in B is deleted; future one kept."""
        fr_a_id = self.fr_a.id
        fr_b_past_id = self.fr_b_past.id
        fr_b_future_id = self.fr_b_future.id
        run_all(today=self.today)
        self.assertFalse(FlightRequest.objects.filter(pk=fr_a_id).exists())
        self.assertFalse(FlightRequest.objects.filter(pk=fr_b_past_id).exists())
        self.assertTrue(FlightRequest.objects.filter(pk=fr_b_future_id).exists())

    def test_script_marks_past_slots_unavailable(self):
        """Slots in period B with date < today are marked unavailable after script."""
        run_all(today=self.today)
        past_slots_b = FlightSlot.objects.filter(
            flight_period=self.period_b,
            date__lt=self.today,
        )
        for slot in past_slots_b:
            slot.refresh_from_db()
            self.assertEqual(slot.status, 'unavailable', f"Slot {slot.id} (date={slot.date}) should be unavailable")

    def test_after_script_low_balance_student_cannot_create_request(self):
        """Student with balance < 500 and no credit cannot create a flight request."""
        run_all(today=self.today)
        period_b_slots = FlightSlot.objects.filter(
            flight_period=self.period_b,
            date__gte=self.today,
            status='available',
        )
        slot = period_b_slots.first()
        self.assertIsNotNone(slot, "Need at least one future available slot")
        req = FlightRequest(student=self.student_low, slot=slot, status='pending')
        with self.assertRaises(ValidationError) as ctx:
            req.full_clean()
        self.assertIn("Balance insuficiente", str(ctx.exception))

    def test_after_script_high_balance_student_can_create_requests_up_to_limit(self):
        """Student with balance 1000 can create up to 2 pending/approved requests."""
        run_all(today=self.today)
        period_b_slots = list(FlightSlot.objects.filter(
            flight_period=self.period_b,
            date__gte=self.today,
            status='available',
        ).order_by('date', 'block')[:3])
        self.assertGreaterEqual(len(period_b_slots), 2, "Need at least 2 future available slots")
        # First request: should succeed
        req1 = FlightRequest(student=self.student_high, slot=period_b_slots[0], status='pending')
        req1.full_clean()
        req1.save()
        period_b_slots[0].status = 'pending'
        period_b_slots[0].student = self.student_high
        period_b_slots[0].save()
        # Second request: should succeed (limit is 2 for balance 1000)
        req2 = FlightRequest(student=self.student_high, slot=period_b_slots[1], status='pending')
        req2.full_clean()
        req2.save()
        # Third request: should fail (max 2)
        req3 = FlightRequest(student=self.student_high, slot=period_b_slots[2], status='pending')
        with self.assertRaises(ValidationError) as ctx:
            req3.full_clean()
        self.assertIn("máximo", str(ctx.exception))

    def test_after_script_credit_student_can_create_up_to_three_requests(self):
        """Student with balance < 500 but has_credit can create up to 3 requests; 4th fails."""
        run_all(today=self.today)
        slots = list(FlightSlot.objects.filter(
            flight_period=self.period_b,
            date__gte=self.today,
            status='available',
        ).order_by('date', 'block')[:4])
        self.assertGreaterEqual(len(slots), 4, "Need at least 4 future available slots")
        # First 3 requests: should succeed (max 3 for credit student)
        for i in range(3):
            req = FlightRequest(student=self.student_credit, slot=slots[i], status='pending')
            req.full_clean()
            req.save()
            slots[i].status = 'pending'
            slots[i].student = self.student_credit
            slots[i].save()
        # Fourth request should fail (max 3 with credit)
        req4 = FlightRequest(student=self.student_credit, slot=slots[3], status='pending')
        with self.assertRaises(ValidationError) as ctx:
            req4.full_clean()
        self.assertIn("máximo", str(ctx.exception))
