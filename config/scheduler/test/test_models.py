from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from datetime import date, timedelta
from scheduler.models import TrainingPeriod, FlightSlot, FlightRequest
from fleet.models import Aircraft
from accounts.models import StudentProfile
from .factories import *

User = get_user_model()

class FlightRequestModelTest(TestCase):
    """Test FlightRequest model methods and business logic."""

    def setUp(self):
        """Set up test data for each test."""
        # Create test aircraft
        self.aircraft = AircraftFactory()
        
        # Create test users
        self.student = UserFactory(role='STUDENT')
        self.student_profile = StudentProfileFactory(user=self.student)
        
        # Create training period
        self.period = TrainingPeriodFactory(aircraft=self.aircraft)
        
        # Generate slots
        self.period.generate_slots()
        self.slot = FlightSlot.objects.filter(training_period=self.period).first()
        
        # Create flight request
        self.flight_request = FlightRequestFactory(
            student=self.student,
            slot=self.slot
        )

    # ===== APPROVE METHOD TESTS =====

    def test_approve_success(self):
        """Test successful flight request approval."""
        # Verify initial state
        self.assertEqual(self.flight_request.status, 'pending')
        self.assertEqual(self.slot.status, 'available')
        self.assertIsNone(self.slot.student)
        
        # Approve the request
        self.flight_request.approve()
        
        # Verify final state
        self.flight_request.refresh_from_db()
        self.slot.refresh_from_db()
        
        self.assertEqual(self.flight_request.status, 'approved')
        self.assertEqual(self.slot.status, 'reserved')
        self.assertEqual(self.slot.student, self.student)

    def test_approve_already_approved_request(self):
        """Test that approving an already approved request raises ValueError."""
        # Set request to approved
        self.flight_request.status = 'approved'
        self.flight_request.save()
        
        # Try to approve again
        with self.assertRaises(ValueError) as context:
            self.flight_request.approve()
        
        self.assertIn("Solo solicitudes pendientes pueden ser aprobadas", str(context.exception))

    def test_approve_cancelled_request(self):
        """Test that approving a cancelled request raises ValueError."""
        # Set request to cancelled
        self.flight_request.status = 'cancelled'
        self.flight_request.save()
        
        # Try to approve
        with self.assertRaises(ValueError) as context:
            self.flight_request.approve()
        
        self.assertIn("Solo solicitudes pendientes pueden ser aprobadas", str(context.exception))

    def test_approve_slot_already_reserved(self):
        """Test that approving a request for an already reserved slot raises ValueError."""
        # Reserve the slot
        self.slot.status = 'reserved'
        self.slot.student = UserFactory(role='STUDENT')
        self.slot.save()
        
        # Try to approve request for reserved slot
        with self.assertRaises(ValueError) as context:
            self.flight_request.approve()
        
        self.assertIn("La sesión de vuelo ya está reservada", str(context.exception))

    def test_approve_insufficient_balance(self):
        """Test that approving a request with insufficient balance raises ValueError."""
        # Set student balance below minimum
        self.student_profile.balance = 400.00
        self.student_profile.save()
        
        # Try to approve
        with self.assertRaises(ValueError) as context:
            self.flight_request.approve()
        
        self.assertIn("Balance insuficiente para aprobar", str(context.exception))

    def test_approve_missing_student_profile(self):
        """Test that approving a request when student has no profile raises ValueError."""
        # Delete student profile
        self.student_profile.delete()
        # Refresh the user from database to clear cached relationships
        self.student.refresh_from_db()

        # Try to approve
        with self.assertRaises(ValueError) as context:
            self.flight_request.approve()
        
        self.assertIn("No se pudo verificar el balance del estudiante", str(context.exception))

    def test_approve_with_original_status_parameter(self):
        """Test the approve method with the original_status parameter."""
        # Set request to approved but pass original_status as pending
        self.flight_request.status = 'approved'
        self.flight_request.save()
        
        # Reset slot to available for this test
        self.slot.status = 'available'
        self.slot.student = None
        self.slot.save()
        
        # Approve with original_status parameter
        self.flight_request.approve(original_status='pending')
        
        # Verify it worked
        self.flight_request.refresh_from_db()
        self.slot.refresh_from_db()
        
        self.assertEqual(self.flight_request.status, 'approved')
        self.assertEqual(self.slot.status, 'reserved')
        self.assertEqual(self.slot.student, self.student)

    def test_approve_balance_exactly_minimum(self):
        """Test that approving with exactly minimum balance ($500) works."""
        # Set student balance to exactly minimum
        self.student_profile.balance = 500.00
        self.student_profile.save()
        
        # Approve should work
        self.flight_request.approve()
        
        # Verify success
        self.flight_request.refresh_from_db()
        self.slot.refresh_from_db()
        
        self.assertEqual(self.flight_request.status, 'approved')
        self.assertEqual(self.slot.status, 'reserved')
        self.assertEqual(self.slot.student, self.student)

    def test_approve_balance_above_minimum(self):
        """Test that approving with balance above minimum works."""
        # Set student balance above minimum
        self.student_profile.balance = 1000.00
        self.student_profile.save()
        
        # Approve should work
        self.flight_request.approve()
        
        # Verify success
        self.flight_request.refresh_from_db()
        self.slot.refresh_from_db()
        
        self.assertEqual(self.flight_request.status, 'approved')
        self.assertEqual(self.slot.status, 'reserved')
        self.assertEqual(self.slot.student, self.student)

    def test_approve_atomic_transaction_rollback(self):
        """Test that if slot update fails, flight request status is not changed."""
        from unittest.mock import patch
        
        # Mock the slot save to raise an exception
        with patch.object(self.slot, 'save', side_effect=Exception("Database error")):
            with self.assertRaises(Exception):
                self.flight_request.approve()
        
        # Verify that flight request status was not changed
        self.flight_request.refresh_from_db()
        self.assertEqual(self.flight_request.status, 'pending')
        
        # Verify slot was not changed
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'available')
        self.assertIsNone(self.slot.student)

    def test_approve_updates_timestamps(self):
        """Test that approve method updates the updated_at timestamp."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Get original timestamp
        original_updated_at = self.flight_request.updated_at
        
        # Wait a small amount to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        # Approve the request
        self.flight_request.approve()
        
        # Verify timestamp was updated
        self.flight_request.refresh_from_db()
        self.assertGreater(self.flight_request.updated_at, original_updated_at)

    def test_approve_with_different_student_balance_scenarios(self):
        """Test approve with various balance scenarios."""
        balance_scenarios = [
            (499.99, False, "Should fail with balance just below minimum"),
            (500.00, True, "Should succeed with exact minimum balance"),
            (500.01, True, "Should succeed with balance just above minimum"),
            (1000.00, True, "Should succeed with high balance"),
        ]
        
        for balance, should_succeed, description in balance_scenarios:
            with self.subTest(balance=balance, description=description):
                # Reset request and slot for each test
                self.flight_request.status = 'pending'
                self.flight_request.save()
                self.slot.status = 'available'
                self.slot.student = None
                self.slot.save()
                
                # Set balance
                self.student_profile.balance = balance
                self.student_profile.save()
                
                if should_succeed:
                    # Should succeed
                    self.flight_request.approve()
                    self.flight_request.refresh_from_db()
                    self.assertEqual(self.flight_request.status, 'approved')
                else:
                    # Should fail
                    with self.assertRaises(ValueError) as context:
                        self.flight_request.approve()
                    self.assertIn("Balance insuficiente", str(context.exception))

    # ===== CANCEL METHOD TESTS =====

    def test_cancel_success(self):
        """Test successful flight request cancellation."""
        # Verify initial state
        self.assertEqual(self.flight_request.status, 'pending')
        self.assertEqual(self.slot.status, 'available')
        self.assertIsNone(self.slot.student)
        
        # Cancel the request
        self.flight_request.cancel()
        
        # Verify final state
        self.flight_request.refresh_from_db()
        self.slot.refresh_from_db()
        
        self.assertEqual(self.flight_request.status, 'cancelled')
        self.assertEqual(self.slot.status, 'available')
        self.assertIsNone(self.slot.student)

    def test_cancel_approved_request(self):
        """Test successful cancellation of an approved request."""
        # First approve the request
        self.flight_request.approve()
        
        # Verify approved state
        self.flight_request.refresh_from_db()
        self.slot.refresh_from_db()
        self.assertEqual(self.flight_request.status, 'approved')
        self.assertEqual(self.slot.status, 'reserved')
        self.assertEqual(self.slot.student, self.student)
        
        # Cancel the approved request
        self.flight_request.cancel()
        
        # Verify final state
        self.flight_request.refresh_from_db()
        self.slot.refresh_from_db()
        
        self.assertEqual(self.flight_request.status, 'cancelled')
        self.assertEqual(self.slot.status, 'available')
        self.assertIsNone(self.slot.student)

    def test_cancel_already_cancelled_request(self):
        """Test that cancelling an already cancelled request raises ValueError."""
        # Set request to cancelled
        self.flight_request.status = 'cancelled'
        self.flight_request.save()
        
        # Try to cancel again
        with self.assertRaises(ValueError) as context:
            self.flight_request.cancel()

        self.assertIn("Solo solicitudes pendientes o aprobadas pueden ser canceladas", str(context.exception))

    def test_cancel_with_invalid_status(self):
        """Test that cancelling a request with invalid status raises ValueError."""
        # Test with a non-existent status
        self.flight_request.status = 'invalid_status'
        self.flight_request.save()
        
        # Try to cancel
        with self.assertRaises(ValueError) as context:
            self.flight_request.cancel()
        
        self.assertIn("Solo solicitudes pendientes o aprobadas pueden ser canceladas", str(context.exception))

    def test_cancel_atomic_transaction_rollback(self):
        """Test that if slot update fails, flight request status is not changed."""
        from unittest.mock import patch
        
        # First approve the request to reserve the slot
        self.flight_request.approve()
        
        # Verify the slot is now reserved
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'reserved')
        self.assertEqual(self.slot.student, self.student)
        
        # Mock the slot save to raise an exception
        with patch.object(self.slot, 'save', side_effect=Exception("Database error")):
            with self.assertRaises(Exception):
                self.flight_request.cancel()
        
        # Verify that flight request status was not changed (still approved)
        self.flight_request.refresh_from_db()
        self.assertEqual(self.flight_request.status, 'approved')
        
        # Verify slot was not changed (still reserved)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'reserved')
        self.assertEqual(self.slot.student, self.student)

    def test_cancel_updates_timestamps(self):
        """Test that cancel method updates the updated_at timestamp."""
        # Get original timestamp
        original_updated_at = self.flight_request.updated_at
        
        # Wait a small amount to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        # Cancel the request
        self.flight_request.cancel()
        
        # Verify timestamp was updated
        self.flight_request.refresh_from_db()
        self.assertGreater(self.flight_request.updated_at, original_updated_at)

    def test_cancel_with_different_status_scenarios(self):
        """Test cancel with various status scenarios."""
        status_scenarios = [
            ('pending', True, "Should succeed with pending status"),
            ('approved', True, "Should succeed with approved status"),
            ('cancelled', False, "Should fail with cancelled status"),
            ('invalid', False, "Should fail with invalid status"),
        ]
        
        for status, should_succeed, description in status_scenarios:
            with self.subTest(status=status, description=description):
                # Reset request and slot for each test
                self.flight_request.status = status
                self.flight_request.save()
                self.slot.status = 'available'
                self.slot.student = None
                self.slot.save()
                
                if should_succeed:
                    # Should succeed
                    self.flight_request.cancel()
                    self.flight_request.refresh_from_db()
                    self.assertEqual(self.flight_request.status, 'cancelled')
                else:
                    # Should fail
                    with self.assertRaises(ValueError) as context:
                        self.flight_request.cancel()
                    self.assertIn("Solo solicitudes pendientes o aprobadas pueden ser canceladas", str(context.exception))

    def test_cancel_workflow_pending_to_cancelled(self):
        """Test the complete workflow: create → cancel."""
        # Verify initial state
        self.assertEqual(self.flight_request.status, 'pending')
        self.assertEqual(self.slot.status, 'available')
        self.assertIsNone(self.slot.student)
        
        # Cancel the request
        self.flight_request.cancel()
        
        # Verify cancelled state
        self.flight_request.refresh_from_db()
        self.slot.refresh_from_db()
        
        self.assertEqual(self.flight_request.status, 'cancelled')
        self.assertEqual(self.slot.status, 'available')
        self.assertIsNone(self.slot.student)

    def test_cancel_workflow_approved_to_cancelled(self):
        """Test the complete workflow: create → approve → cancel."""
        # First approve the request
        self.flight_request.approve()
        
        # Verify approved state
        self.flight_request.refresh_from_db()
        self.slot.refresh_from_db()
        self.assertEqual(self.flight_request.status, 'approved')
        self.assertEqual(self.slot.status, 'reserved')
        self.assertEqual(self.slot.student, self.student)
        
        # Cancel the approved request
        self.flight_request.cancel()
        
        # Verify cancelled state
        self.flight_request.refresh_from_db()
        self.slot.refresh_from_db()
        
        self.assertEqual(self.flight_request.status, 'cancelled')
        self.assertEqual(self.slot.status, 'available')
        self.assertIsNone(self.slot.student)

    def test_cancel_slot_availability_after_cancel(self):
        """Test that a slot becomes available again after cancelling a request."""
        # First approve the request to reserve the slot
        self.flight_request.approve()
        
        # Verify slot is reserved
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'reserved')
        self.assertEqual(self.slot.student, self.student)
        
        # Cancel the request
        self.flight_request.cancel()
        
        # Verify slot is available again
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'available')
        self.assertIsNone(self.slot.student)