from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
from unittest.mock import patch
from scheduler.models import FlightPeriod, FlightSlot, FlightRequest
from scheduler.exceptions import (
    PeriodNotActiveError, SlotNotAvailableError, InsufficientBalanceError, MaxRequestsExceededError
)
from .factories import *

User = get_user_model()


class FlightRequestViewTest(TestCase):
    """Test flight request view functionality."""

    def setUp(self):
        """Set up test data for each test."""
        self.client = Client()
        
        # Create users
        self.student = UserFactory()
        self.staff = StaffUserFactory()
        
        # Create student profile
        self.student_profile = StudentProfileFactory(user=self.student, balance=1000.00)
        
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
        
        # Create a flight request with insufficient balance
        self.student_profile.balance = 400.00
        self.student_profile.save()
        
        flight_request = FlightRequestFactory(
            student=self.student,
            slot=self.slot,
            status='pending'
        )
        
        response = self.client.post(
            reverse('scheduler:approve_flight_request', args=[flight_request.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)

    def test_cancel_flight_request_success(self):
        """Test successful flight request cancellation."""
        self.client.force_login(self.staff)
        
        # Create a flight request
        flight_request = FlightRequestFactory(
            student=self.student,
            slot=self.slot,
            status='pending'
        )
        
        response = self.client.post(
            reverse('scheduler:cancel_flight_request', args=[flight_request.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('Solicitud de vuelo cancelada exitosamente', data['message'])

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
        
        data = {
            'start_date': '2024-01-01',  # Monday
            'end_date': '2024-01-07',    # Sunday
            'aircraft': self.aircraft.id,
            'is_active': False
        }
        
        response = self.client.post(reverse('scheduler:create_flight_period'), data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(FlightPeriod.objects.filter(aircraft=self.aircraft).exists())

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
        """Test handling of validation errors in flight period creation."""
        self.client.force_login(self.staff)
        
        # Invalid data - end date before start date
        data = {
            'start_date': '2024-01-07',
            'end_date': '2024-01-01',
            'aircraft': self.aircraft.id,
            'is_active': False
        }
        
        response = self.client.post(reverse('scheduler:create_flight_period'), data)
        
        self.assertEqual(response.status_code, 200)  # Form is re-rendered with errors
        self.assertFalse(FlightPeriod.objects.filter(aircraft=self.aircraft).exists())

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

    def test_activate_flight_period_conflict(self):
        """Test activation when another period is already active for the same aircraft."""
        self.client.force_login(self.staff)
        
        # Create an active period
        active_period = FlightPeriodFactory(aircraft=self.aircraft, is_active=True)
        
        # Try to activate another period for the same aircraft
        new_period = FlightPeriodFactory(aircraft=self.aircraft, is_active=False)
        
        response = self.client.post(
            reverse('scheduler:activate_flight_period', args=[new_period.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('Ya existe un período activo', data['error'])


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
