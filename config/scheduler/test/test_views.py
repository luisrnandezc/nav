import json
from django.core import mail
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from accounts.models import StudentProfile
from scheduler.models import FlightPeriod, FlightRequest
from .factories import *
from datetime import date, timedelta

User = get_user_model()


class FlightRequestViewTest(TestCase):
    """Test flight request view functionality."""

    def setUp(self):
        """Set up test data for each test."""
        self.client = Client()
        
        # Create users
        self.student = UserFactory()
        self.staff = StaffUserFactory()
        
        # Create student profile (flying phase only appear in staff FR student list)
        self.student_profile = StudentProfileFactory(
            user=self.student,
            balance=1000.00,
            student_phase=StudentProfile.FLYING,
        )
        
        # Create test data
        self.aircraft = AircraftFactory()
        self.period = FlightPeriodFactory(aircraft=self.aircraft, is_active=True)
        self.slot = FlightSlotFactory(flight_period=self.period, status='available')

    def test_create_flight_request_success(self):
        """Test successful flight request creation."""
        self.client.force_login(self.student)
        
        response = self.client.post(
            reverse('scheduler:create_flight_request', args=[self.slot.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('Solicitud de vuelo creada exitosamente', data['message'])
        
        # Verify request was created
        self.assertTrue(FlightRequest.objects.filter(student=self.student, slot=self.slot).exists())

    def test_create_flight_request_unauthorized(self):
        """Test that non-students cannot create flight requests."""
        self.client.force_login(self.staff)
        
        response = self.client.post(
            reverse('scheduler:create_flight_request', args=[self.slot.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn('Acceso denegado', data['error'])

    def test_create_flight_request_not_logged_in(self):
        """Test that anonymous users cannot create flight requests."""
        response = self.client.post(
            reverse('scheduler:create_flight_request', args=[self.slot.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_create_flight_request_validation_error(self):
        """Test handling of validation errors in flight request creation."""
        self.client.force_login(self.student)
        
        # Make slot unavailable
        self.slot.status = 'unavailable'
        self.slot.save()
        
        response = self.client.post(
            reverse('scheduler:create_flight_request', args=[self.slot.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)

    def test_create_flight_request_period_not_active_error(self):
        """Test handling of PeriodNotActiveError in flight request creation."""
        self.client.force_login(self.student)
        
        # Make period inactive
        self.period.is_active = False
        self.period.save()
        
        response = self.client.post(
            reverse('scheduler:create_flight_request', args=[self.slot.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)

    def test_staff_create_approved_flight_request_get_success(self):
        """Staff can open the staff-create flight request form for a slot."""
        self.client.force_login(self.staff)
        response = self.client.get(
            reverse('scheduler:staff_create_approved_flight_request', args=[self.slot.id]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Crear solicitud aprobada')

    def test_staff_create_approved_flight_request_get_forbidden_for_student(self):
        self.client.force_login(self.student)
        response = self.client.get(
            reverse('scheduler:staff_create_approved_flight_request', args=[self.slot.id]),
        )
        self.assertEqual(response.status_code, 403)

    def test_staff_create_approved_flight_request_get_redirects_if_anonymous(self):
        response = self.client.get(
            reverse('scheduler:staff_create_approved_flight_request', args=[self.slot.id]),
        )
        self.assertEqual(response.status_code, 302)

    def test_staff_create_approved_flight_request_post_success(self):
        """Staff POST creates an approved FlightRequest and stays on the same page."""
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse('scheduler:staff_create_approved_flight_request', args=[self.slot.id]),
            {'student': self.student.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Solicitud de vuelo creada y aprobada exitosamente')
        self.assertContains(response, 'ya no está disponible')
        self.assertTrue(
            FlightRequest.objects.filter(
                student=self.student,
                slot=self.slot,
                status='approved',
            ).exists()
        )
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'reserved')
        self.assertEqual(self.slot.student, self.student)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='scheduler-from@test.com',
        OPS_NOTIFICATION_EMAIL='ops-notify@test.com',
    )
    def test_staff_create_approved_flight_request_sends_student_session_email(self):
        """Student receives session email when staff creates an approved request."""
        self.client.force_login(self.staff)
        mail.outbox.clear()
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(
                reverse('scheduler:staff_create_approved_flight_request', args=[self.slot.id]),
                {'student': self.student.pk},
            )
        student_messages = [m for m in mail.outbox if list(m.to) == [self.student.email]]
        self.assertEqual(len(student_messages), 1)
        self.assertIn('Sesión de vuelo asignada', student_messages[0].subject)
        self.assertIn(self.slot.aircraft.registration, student_messages[0].body)

    def test_staff_create_approved_flight_request_post_shows_slot_error(self):
        """When the slot is not available, the form is re-rendered with an error."""
        self.client.force_login(self.staff)
        self.slot.status = 'reserved'
        self.slot.save()
        response = self.client.post(
            reverse('scheduler:staff_create_approved_flight_request', args=[self.slot.id]),
            {'student': self.student.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'disponible')

    def test_approve_flight_request_success(self):
        """Test successful flight request approval."""
        self.client.force_login(self.staff)
        
        # Create a flight request
        flight_request = FlightRequestFactory(
            student=self.student,
            slot=self.slot,
            status='pending'
        )
        
        response = self.client.post(
            reverse('scheduler:approve_flight_request', args=[flight_request.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('Solicitud de vuelo aprobada exitosamente', data['message'])

    def test_approve_flight_request_unauthorized(self):
        """Test that non-staff cannot approve flight requests."""
        self.client.force_login(self.student)
        
        flight_request = FlightRequestFactory(
            student=self.student,
            slot=self.slot,
            status='pending'
        )
        
        response = self.client.post(
            reverse('scheduler:approve_flight_request', args=[flight_request.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn('Acceso denegado', data['error'])

    def test_approve_flight_request_validation_error(self):
        """Test handling of validation errors in flight request approval."""
        self.client.force_login(self.staff)
        
        # Ensure student has sufficient balance to create the request
        self.student_profile.balance = 1000.00
        self.student_profile.save()

        # Create a valid pending request
        flight_request = FlightRequestFactory(
            student=self.student,
            slot=self.slot,
            status='pending'
        )

        # Now reduce balance so approval should fail the secondary check
        self.student_profile.balance = 400.00
        self.student_profile.save()

        response = self.client.post(
            reverse('scheduler:approve_flight_request', args=[flight_request.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)

    def test_cancel_flight_request_success_as_staff(self):
        """Staff should be able to cancel a pending flight request."""
        self.client.force_login(self.staff)

        flight_request = FlightRequestFactory(
            student=self.student,
            slot=self.slot,
            status='pending'
        )

        response = self.client.post(
            reverse('scheduler:cancel_flight_request', args=[flight_request.id]),
            data=json.dumps({}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('Solicitud de vuelo cancelada exitosamente', data['message'])

        # Verify state changes
        flight_request.refresh_from_db()
        self.assertEqual(flight_request.status, 'cancelled')
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'available')

    def test_cancel_flight_request_success_as_student(self):
        """Student should be able to cancel their own pending flight request."""
        self.client.force_login(self.student)

        flight_request = FlightRequestFactory(
            student=self.student,
            slot=self.slot,
            status='pending'
        )

        response = self.client.post(
            reverse('scheduler:cancel_flight_request', args=[flight_request.id]),
            data=json.dumps({}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('Solicitud de vuelo cancelada exitosamente', data['message'])

        # Verify state changes
        flight_request.refresh_from_db()
        self.assertEqual(flight_request.status, 'cancelled')
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'available')

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='scheduler-from@test.com',
        OPS_NOTIFICATION_EMAIL='ops-notify@test.com',
    )
    def test_cancel_by_student_emails_staff_not_student(self):
        """Student cancel: ops gets 'student cancelled' mail; student does not get cancel mail."""
        mail.outbox.clear()
        self.client.force_login(self.student)
        flight_request = FlightRequestFactory(
            student=self.student,
            slot=self.slot,
            status='pending',
        )
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse('scheduler:cancel_flight_request', args=[flight_request.id]),
                data=json.dumps({}),
                content_type='application/json',
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            )
        self.assertEqual(response.status_code, 200)
        to_ops = [m for m in mail.outbox if 'ops-notify@test.com' in m.to]
        self.assertTrue(to_ops, 'Expected mail to OPS_NOTIFICATION_EMAIL')
        self.assertIn('El estudiante ha cancelado', to_ops[0].body)
        to_student = [m for m in mail.outbox if self.student.email in m.to]
        cancel_to_student = [m for m in to_student if 'Solicitud de vuelo cancelada' in m.subject]
        self.assertEqual(cancel_to_student, [])

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='scheduler-from@test.com',
        OPS_NOTIFICATION_EMAIL='ops-notify@test.com',
    )
    def test_cancel_by_staff_emails_student_not_ops_student_cancelled(self):
        """Staff cancel: student gets mail; ops does not get 'student cancelled' mail."""
        mail.outbox.clear()
        self.client.force_login(self.staff)
        flight_request = FlightRequestFactory(
            student=self.student,
            slot=self.slot,
            status='pending',
        )
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse('scheduler:cancel_flight_request', args=[flight_request.id]),
                data=json.dumps({}),
                content_type='application/json',
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            )
        self.assertEqual(response.status_code, 200)
        to_student = [m for m in mail.outbox if self.student.email in m.to]
        self.assertTrue(to_student, 'Expected mail to student')
        self.assertIn('Solicitud de vuelo cancelada', to_student[0].subject)
        self.assertIn('cancelada por la escuela', to_student[0].body)
        to_ops = [m for m in mail.outbox if 'ops-notify@test.com' in m.to]
        self.assertEqual(to_ops, [])

    def test_cancel_flight_request_validation_error(self):
        """Test handling of validation errors in flight request cancellation."""
        self.client.force_login(self.staff)
        
        # Create a flight request with invalid status
        flight_request = FlightRequestFactory(
            student=self.student,
            slot=self.slot,
            status='cancelled'  # Already cancelled
        )
        
        response = self.client.post(
            reverse('scheduler:cancel_flight_request', args=[flight_request.id]),
            data=json.dumps({}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)


class FlightPeriodViewTest(TestCase):
    """Test flight period view functionality."""

    def setUp(self):
        """Set up test data for each test."""
        self.client = Client()
        self.staff = StaffUserFactory()
        self.student = UserFactory()
        self.aircraft = AircraftFactory()

    def test_create_flight_period_success(self):
        """Test successful flight period creation."""
        self.client.force_login(self.staff)
        
        # Use next Monday to next Sunday (valid 7-day period in the near future)
        today = date.today()
        days_to_next_monday = (7 - today.weekday()) % 7 or 7  # Monday=0
        start_date = today + timedelta(days=days_to_next_monday)
        end_date = start_date + timedelta(days=6)

        data = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'aircraft': self.aircraft.id,
            'is_active': False
        }
        
        response = self.client.post(reverse('scheduler:create_flight_period'), data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(FlightPeriod.objects.filter(aircraft=self.aircraft, start_date=start_date, end_date=end_date).exists())

    def test_create_flight_period_unauthorized(self):
        """Test that non-staff cannot create flight periods."""
        self.client.force_login(self.student)
        
        data = {
            'start_date': '2024-01-01',
            'end_date': '2024-01-07',
            'aircraft': self.aircraft.id,
            'is_active': False
        }
        
        response = self.client.post(reverse('scheduler:create_flight_period'), data)
        
        self.assertEqual(response.status_code, 403)

    def test_create_flight_period_validation_error(self):
        """View should not create a period when length is not multiple of 7."""
        self.client.force_login(self.staff)

        # Build a period starting next Monday and ending on Saturday (6-day span -> invalid)
        today = date.today()
        days_to_next_monday = (7 - today.weekday()) % 7 or 7  # Monday=0
        start_date = today + timedelta(days=days_to_next_monday)
        end_date = start_date + timedelta(days=5)  # 6 days total, not multiple of 7

        before = FlightPeriod.objects.count()

        response = self.client.post(reverse('scheduler:create_flight_period'), {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'aircraft': self.aircraft.id,
            'is_active': False,
        })

        # Form should re-render with errors and no new record should be created
        self.assertEqual(response.status_code, 200)
        self.assertEqual(FlightPeriod.objects.count(), before)

    def test_activate_flight_period_success(self):
        """Test successful flight period activation."""
        self.client.force_login(self.staff)
        
        period = FlightPeriodFactory(aircraft=self.aircraft, is_active=False)
        
        response = self.client.post(
            reverse('scheduler:activate_flight_period', args=[period.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify period is activated
        period.refresh_from_db()
        self.assertTrue(period.is_active)

    def test_activate_flight_period_already_active(self):
        """Test activation of already active period."""
        self.client.force_login(self.staff)
        
        period = FlightPeriodFactory(aircraft=self.aircraft, is_active=True)
        
        response = self.client.post(
            reverse('scheduler:activate_flight_period', args=[period.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('Este período ya está activo', data['error'])


class ChangeSlotStatusViewTest(TestCase):
    """Test change slot status view functionality."""

    def setUp(self):
        """Set up test data for each test."""
        self.client = Client()
        self.staff = StaffUserFactory()
        self.student = UserFactory()
        self.aircraft = AircraftFactory()
        self.period = FlightPeriodFactory(aircraft=self.aircraft)
        self.slot = FlightSlotFactory(flight_period=self.period, status='available')

    def test_change_slot_status_success(self):
        """Test successful slot status change."""
        self.client.force_login(self.staff)
        
        data = {
            'action': 'unavailable',
            'new_status': 'unavailable'
        }
        
        response = self.client.post(
            reverse('scheduler:change_slot_status', args=[self.slot.id]),
            data,
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify slot status changed
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'unavailable')

    def test_change_slot_status_unauthorized(self):
        """Test that non-staff cannot change slot status."""
        self.client.force_login(self.student)
        
        data = {
            'action': 'unavailable',
            'new_status': 'unavailable'
        }
        
        response = self.client.post(
            reverse('scheduler:change_slot_status', args=[self.slot.id]),
            data,
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 403)

    def test_change_slot_status_invalid_json(self):
        """Test handling of invalid JSON data."""
        self.client.force_login(self.staff)
        
        response = self.client.post(
            reverse('scheduler:change_slot_status', args=[self.slot.id]),
            'invalid json',
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('Datos JSON inválidos', data['error'])

    def test_change_slot_status_missing_data(self):
        """Test handling of missing required data."""
        self.client.force_login(self.staff)
        
        data = {
            'action': 'unavailable'
            # Missing new_status
        }
        
        response = self.client.post(
            reverse('scheduler:change_slot_status', args=[self.slot.id]),
            data,
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('Acción y nuevo estado requeridos', data['error'])
