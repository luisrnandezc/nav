from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import StudentProfile
from scheduler.domain_signals import FLIGHT_REQUEST_CANCELLED_BY_STAFF
from scheduler.models import FlightRequest
from .factories import (
    FlightPeriodFactory,
    FlightSlotFactory,
    StaffUserFactory,
    StudentProfileFactory,
    UserFactory,
)


class FlightRequestBlockingTest(TestCase):
    message = 'No tienes permiso para solicitar vuelos. Contacta con administración.'

    def setUp(self):
        self.student = UserFactory()
        self.profile = StudentProfileFactory(
            user=self.student,
            student_phase=StudentProfile.FLYING,
            balance=1000,
        )
        self.period = FlightPeriodFactory(is_active=True)
        self.slot = FlightSlotFactory(flight_period=self.period)

    def set_blocked(self, blocked=True, **changes):
        self.profile.flight_requests_blocked = blocked
        for name, value in changes.items():
            setattr(self.profile, name, value)
        self.profile.save()

    def assert_no_booking(self):
        self.assertFalse(FlightRequest.objects.exists())
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'available')
        self.assertIsNone(self.slot.student_id)

    def test_default_allows_booking(self):
        self.assertFalse(self.profile.flight_requests_blocked)
        request = FlightRequest()
        request.create_request(self.student, self.slot)
        self.assertEqual(request.status, 'pending')
        self.assertTrue(FlightRequest.objects.filter(pk=request.pk).exists())

    def test_block_overrides_balance_and_financial_exceptions(self):
        for balance, credit, temporary in [(1000, False, False), (0, True, False), (0, False, True)]:
            with self.subTest(balance=balance, credit=credit, temporary=temporary):
                self.set_blocked(balance=balance, has_credit=credit, has_temp_permission=temporary)
                with self.assertRaisesMessage(ValidationError, self.message):
                    FlightRequest().create_request(self.student, self.slot)
                self.assert_no_booking()

    def test_direct_model_creation_is_blocked_even_with_explicit_pk(self):
        self.set_blocked()
        with self.assertRaisesMessage(ValidationError, self.message):
            FlightRequest.objects.create(pk=12345, student=self.student, slot=self.slot)
        self.assert_no_booking()

    def test_staff_booking_is_blocked_without_consuming_temporary_permission(self):
        self.set_blocked(balance=0, has_temp_permission=True)
        with self.assertRaisesMessage(ValidationError, self.message):
            FlightRequest.create_approved_by_staff(self.student, self.slot)
        self.assert_no_booking()
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.has_temp_permission)

    def test_existing_request_can_be_edited_approved_and_cancelled(self):
        request = FlightRequest()
        request.create_request(self.student, self.slot)
        self.set_blocked()
        request.notes = 'Existing request remains editable'
        request.save()
        request.approve()
        request.refresh_from_db()
        self.assertEqual(request.status, 'approved')
        self.assertEqual(request.notes, 'Existing request remains editable')
        request.cancel(cancelled_by=FLIGHT_REQUEST_CANCELLED_BY_STAFF)
        request.refresh_from_db()
        self.assertEqual(request.status, 'cancelled')

    def test_unblocking_restores_booking_and_keeps_financial_rules(self):
        self.set_blocked()
        self.set_blocked(False, balance=0)
        with self.assertRaisesMessage(ValidationError, 'Balance insuficiente'):
            FlightRequest().create_request(self.student, self.slot)
        self.assert_no_booking()
        self.set_blocked(False, balance=1000)
        request = FlightRequest()
        request.create_request(self.student, self.slot)
        self.assertIsNotNone(request.pk)

    def test_student_post_cannot_bypass_ui(self):
        self.set_blocked()
        self.client.force_login(self.student)
        response = self.client.post(reverse('scheduler:create_flight_request', args=[self.slot.pk]))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], self.message)
        self.assert_no_booking()

    def test_staff_post_cannot_bypass_block(self):
        self.set_blocked()
        self.client.force_login(StaffUserFactory())
        response = self.client.post(
            reverse('scheduler:staff_create_approved_flight_request', args=[self.slot.pk]),
            {'student': self.student.pk},
        )
        self.assertContains(response, self.message)
        self.assert_no_booking()

    def test_dashboard_disables_booking_but_remains_accessible(self):
        self.set_blocked()
        self.client.force_login(self.student)
        response = self.client.get(reverse('scheduler:student_flight_requests_dashboard'))
        self.assertContains(response, self.message)
        self.assertContains(response, '<button class="button" type="button" disabled>Agendar vuelo</button>', html=True)
        self.assertNotContains(response, 'href="' + reverse('scheduler:create_student_flight_period_grids') + '"')

    def test_direct_grid_visit_has_no_clickable_slots_until_unblocked(self):
        self.set_blocked()
        self.client.force_login(self.student)
        url = reverse('scheduler:create_student_flight_period_grids')
        response = self.client.get(url)
        self.assertContains(response, self.message)
        self.assertNotContains(response, 'clickable-slot')
        self.assertNotContains(response, 'data-slot-id=')
        self.set_blocked(False)
        response = self.client.get(url)
        self.assertNotContains(response, self.message)
        self.assertContains(response, 'clickable-slot')
