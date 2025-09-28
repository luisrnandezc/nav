from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from scheduler.models import FlightPeriod, FlightSlot, FlightRequest
from scheduler.exceptions import (
    InvalidPeriodDurationError, PeriodOverlapError, AircraftNotAvailableError,
    PeriodNotActiveError, SlotNotAvailableError, InsufficientBalanceError,
)
from .factories import *

User = get_user_model()

class FlightPeriodModelTest(TestCase):
    """Test FlightPeriod model methods and business logic."""

    def setUp(self):
        """Set up test data for each test."""
        self.aircraft = AircraftFactory()
        self.period = FlightPeriodFactory()

    def test_generate_slots_creates_correct_number(self):
        """Test that generate_slots creates the correct number of slots."""
        # FlightPeriodFactory creates 7 days (today + 6 days) × 3 blocks = 21 slots
        created_count = self.period.generate_slots()
        self.assertEqual(created_count, 21)
        
        # Verify slots were actually created in database
        slots = FlightSlot.objects.filter(flight_period=self.period)
        self.assertEqual(slots.count(), 21)

    def test_generate_slots_creates_all_blocks(self):
        """Test that generate_slots creates all three blocks for each day."""
        self.period.generate_slots()
        
        # Check that all 3 blocks exist for the first day
        first_day_slots = FlightSlot.objects.filter(
            flight_period=self.period,
            date=self.period.start_date
        )
        self.assertEqual(first_day_slots.count(), 3)
        
        # Verify all blocks are present
        blocks = set(first_day_slots.values_list('block', flat=True))
        self.assertEqual(blocks, {'AM', 'M', 'PM'})

    def test_generate_slots_sets_correct_attributes(self):
        """Test that generated slots have correct attributes."""
        self.period.generate_slots()
        slot = FlightSlot.objects.filter(flight_period=self.period).first()
        
        self.assertEqual(slot.status, 'available')
        self.assertEqual(slot.flight_period, self.period)
        self.assertIsNone(slot.instructor)
        self.assertIsNone(slot.student)
        self.assertEqual(slot.date, self.period.start_date)
        self.assertEqual(slot.block, 'AM')

    def test_generate_slots_creates_slots_for_all_days(self):
        """Test that generate_slots creates slots for all days in the period."""
        self.period.generate_slots()
        
        # Check that slots exist for each day in the period
        current_date = self.period.start_date
        while current_date <= self.period.end_date:
            day_slots = FlightSlot.objects.filter(
                flight_period=self.period,
                date=current_date
            )
            self.assertEqual(day_slots.count(), 3, f"Expected 3 slots for {current_date}")
            current_date += timedelta(days=1)

    def test_generate_slots_returns_created_count(self):
        """Test that generate_slots returns the number of created slots."""
        created_count = self.period.generate_slots()
        self.assertEqual(created_count, 21)
        
        # Verify slots were actually created in database
        total_slots = FlightSlot.objects.filter(flight_period=self.period).count()
        self.assertEqual(total_slots, 21)

    def test_str_representation(self):
        """Test that the __str__ method returns the correct string."""
        expected_str = f"Periodo: {self.period.start_date} → {self.period.end_date}"
        self.assertEqual(str(self.period), expected_str)

    def test_model_meta_ordering(self):
        """Test that the model is ordered by start_date descending."""
        # Create multiple periods with different dates and different aircraft to avoid overlap
        aircraft2 = AircraftFactory()
        period1 = FlightPeriodFactory(
            aircraft=self.aircraft,
            start_date=date.today()
        )
        period2 = FlightPeriodFactory(
            aircraft=aircraft2,
            start_date=date.today() + timedelta(days=7)  # 1 week later to avoid overlap
        )
        
        # Query all periods
        periods = list(FlightPeriod.objects.all())
        
        # Should be ordered by start_date descending (newest first)
        # Find our periods in the results
        period1_found = None
        period2_found = None
        for i, period in enumerate(periods):
            if period.id == period1.id:
                period1_found = i
            elif period.id == period2.id:
                period2_found = i
        
        # period2 should come before period1 (newer date first)
        self.assertIsNotNone(period1_found)
        self.assertIsNotNone(period2_found)
        self.assertLess(period2_found, period1_found)

    def test_foreign_key_relationship(self):
        """Test the foreign key relationship with Aircraft."""
        # Create a period with the specific aircraft
        period = FlightPeriodFactory(aircraft=self.aircraft)
        self.assertEqual(period.aircraft, self.aircraft)
        
        # Test reverse relationship
        aircraft_periods = self.aircraft.flight_periods.all()
        self.assertIn(period, aircraft_periods)

    def test_model_fields(self):
        """Test that all model fields are properly set."""
        # Test required fields
        self.assertIsNotNone(self.period.start_date)
        self.assertIsNotNone(self.period.end_date)
        self.assertIsNotNone(self.period.aircraft)
        
        # Test default values
        self.assertFalse(self.period.is_active)
        self.assertIsNotNone(self.period.created_at)
        self.assertIsNotNone(self.period.updated_at)

    def test_period_duration(self):
        """Test that the period duration is calculated correctly."""
        # FlightPeriodFactory creates 7-day periods
        duration = (self.period.end_date - self.period.start_date).days
        self.assertEqual(duration, 6)  # 6 days difference (7 days total)

    def test_generate_slots_with_different_period_lengths(self):
        """Test generate_slots with different period lengths."""
        # Create a 7-day period (1 week)
        short_period = FlightPeriodFactory(
            aircraft=self.aircraft,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=6)  # 7 days total
        )
        
        created_count = short_period.generate_slots()
        self.assertEqual(created_count, 21)  # 7 days × 3 blocks = 21 slots
        
        # Create a 14-day period (2 weeks) with different aircraft to avoid conflicts
        different_aircraft = AircraftFactory()
        long_period = FlightPeriodFactory(
            aircraft=different_aircraft,
            start_date=date.today() + timedelta(days=14),  # 2 weeks later
            end_date=date.today() + timedelta(days=27)  # 14 days total
        )
        
        created_count = long_period.generate_slots()
        self.assertEqual(created_count, 42)  # 14 days × 3 blocks = 42 slots

    # ===== FIELD CONSTRAINT TESTS =====

    def test_start_date_required(self):
        """Test that start_date is required."""
        with self.assertRaises(TypeError):
            FlightPeriod.objects.create(
                end_date=date.today() + timedelta(days=6),
                aircraft=self.aircraft
            )

    def test_end_date_required(self):
        """Test that end_date is required."""
        with self.assertRaises(TypeError):
            period = FlightPeriod(
                start_date=date.today(),
                aircraft=self.aircraft
            )
            period.full_clean()

    def test_aircraft_required(self):
        """Test that aircraft is required."""
        with self.assertRaises(FlightPeriod.aircraft.RelatedObjectDoesNotExist):
            period = FlightPeriod(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=6),
                aircraft=None
            )
            period.full_clean()

    def test_is_active_default_value(self):
        """Test that is_active defaults to False."""
        period = FlightPeriod.objects.create(
            start_date=date(2025, 9, 27),
            end_date=date(2025, 10, 3),  # Exactly 7 days
            aircraft=self.aircraft
        )
        self.assertFalse(period.is_active)

    def test_created_at_auto_add(self):
        """Test that created_at is automatically set."""
        period = FlightPeriod.objects.create(
            start_date=date(2025, 9, 27),
            end_date=date(2025, 10, 3),  # Exactly 7 days
            aircraft=self.aircraft
        )
        self.assertIsNotNone(period.created_at)
        self.assertLessEqual(period.created_at, timezone.now())

    def test_updated_at_auto_now(self):
        """Test that updated_at is automatically set and updated."""
        # Use the existing period from setUp to avoid overlap
        period = self.period
        
        original_updated_at = period.updated_at
        
        # Wait a small amount and update the period
        import time
        time.sleep(0.01)
        period.is_active = True
        period.save()
        
        self.assertGreater(period.updated_at, original_updated_at)

    def test_aircraft_foreign_key_cascade_delete(self):
        """Test that deleting aircraft cascades to flight periods."""
        period_id = self.period.id
        self.period.aircraft.delete()
        
        # Period should be deleted due to CASCADE
        with self.assertRaises(FlightPeriod.DoesNotExist):
            FlightPeriod.objects.get(id=period_id)

    def test_aircraft_foreign_key_relationship(self):
        """Test the foreign key relationship with Aircraft."""
        period = FlightPeriodFactory(aircraft=self.aircraft)
        
        # Test forward relationship
        self.assertEqual(period.aircraft, self.aircraft)
        
        # Test reverse relationship
        self.assertIn(period, self.aircraft.flight_periods.all())

    def test_period_dates_validation(self):
        """Test that start_date and end_date can be set correctly."""
        period = FlightPeriod.objects.create(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=6),  # 7 days total
            aircraft=self.aircraft
        )
        
        self.assertEqual(period.start_date, date.today())
        self.assertEqual(period.end_date, date.today() + timedelta(days=6))

    # ===== VALIDATION METHOD TESTS =====

    def test_check_flight_period_length_valid(self):
        """Test that valid period lengths pass validation."""
        # Test 1 week (7 days)
        period = FlightPeriod(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=6),
            aircraft=self.aircraft
        )
        # Should not raise exception
        period._check_flight_period_length(period.start_date, period.end_date)

    def test_check_flight_period_length_invalid(self):
        """Test that invalid period lengths raise InvalidPeriodDurationError."""
        # Test 5 days (not multiple of 7)
        period = FlightPeriod(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=4),
            aircraft=self.aircraft
        )
        
        with self.assertRaises(InvalidPeriodDurationError) as context:
            period._check_flight_period_length(period.start_date, period.end_date)
        
        self.assertIn("El periodo debe ser un múltiplo de 7 días", str(context.exception))

    def test_check_flight_period_length_limits_valid(self):
        """Test that valid period length limits pass validation."""
        # Test 1 week (7 days)
        period = FlightPeriod(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=6),
            aircraft=self.aircraft
        )
        # Should not raise exception
        period._check_flight_period_length_limits(period.start_date, period.end_date)

    def test_check_flight_period_length_limits_too_short(self):
        """Test that periods shorter than 7 days raise InvalidPeriodDurationError."""
        # Test 3 days
        period = FlightPeriod(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            aircraft=self.aircraft
        )
        
        with self.assertRaises(InvalidPeriodDurationError) as context:
            period._check_flight_period_length_limits(period.start_date, period.end_date)
        
        self.assertIn("El período no puede ser menor a 7 días", str(context.exception))

    def test_check_flight_period_length_limits_too_long(self):
        """Test that periods longer than 21 days raise InvalidPeriodDurationError."""
        # Test 4 weeks (28 days)
        period = FlightPeriod(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=27),
            aircraft=self.aircraft
        )
        
        with self.assertRaises(InvalidPeriodDurationError) as context:
            period._check_flight_period_length_limits(period.start_date, period.end_date)
        
        self.assertIn("El período no puede ser menor a 7 días ni mayor a 3 semanas", str(context.exception))

    def test_check_flight_period_overlap_no_overlap(self):
        """Test that non-overlapping periods pass validation."""
        # Create existing period
        existing_period = FlightPeriodFactory(
            aircraft=self.aircraft,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=13)
        )
        
        # New period that doesn't overlap
        new_period = FlightPeriod(
            start_date=date.today() + timedelta(days=14),
            end_date=date.today() + timedelta(days=20),
            aircraft=self.aircraft
        )
        
        # Should not raise exception
        new_period._check_flight_period_overlap(
            new_period.start_date, 
            new_period.end_date, 
            new_period.aircraft
        )

    def test_check_flight_period_overlap_with_overlap(self):
        """Test that overlapping periods raise PeriodOverlapError."""
        # Create existing period
        existing_period = FlightPeriodFactory(
            aircraft=self.aircraft,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=13)
        )
        
        # New period that overlaps
        new_period = FlightPeriod(
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=16),
            aircraft=self.aircraft
        )
        
        with self.assertRaises(PeriodOverlapError) as context:
            new_period._check_flight_period_overlap(
                new_period.start_date, 
                new_period.end_date, 
                new_period.aircraft
            )
        
        self.assertIn("El período se superpone con otro período de vuelo", str(context.exception))

    def test_check_aircraft_availability_valid(self):
        """Test that available aircraft pass validation."""
        # Should not raise exception
        FlightPeriod._check_aircraft_availability(None, self.aircraft)

    def test_check_aircraft_availability_invalid(self):
        """Test that unavailable aircraft raise AircraftNotAvailableError."""
        # Make aircraft unavailable
        self.aircraft.is_available = False
        self.aircraft.save()
        
        with self.assertRaises(AircraftNotAvailableError) as context:
            FlightPeriod._check_aircraft_availability(None, self.aircraft)
        
        self.assertIn("La aeronave no está activa o disponible", str(context.exception))

    def test_period_dates_future_validation(self):
        """Test that periods can be created for future dates."""
        future_start = date.today() + timedelta(days=30)
        future_end = future_start + timedelta(days=6)
        
        period = FlightPeriod.objects.create(
            start_date=future_start,
            end_date=future_end,
            aircraft=self.aircraft
        )
        
        self.assertEqual(period.start_date, future_start)
        self.assertEqual(period.end_date, future_end)

    def test_period_dates_past_validation(self):
        """Test that periods cannot be created for past dates."""
        past_start = date.today() - timedelta(days=30)
        past_end = past_start + timedelta(days=6)  # 7 days total
        
        with self.assertRaises(ValidationError) as context:
            period = FlightPeriod(
                start_date=past_start,
                end_date=past_end,
                aircraft=self.aircraft
            )
            period.full_clean()
        
        self.assertIn("La fecha de inicio no puede ser anterior a hoy", str(context.exception))

    def test_model_verbose_names(self):
        """Test that model has correct verbose names."""
        self.assertEqual(FlightPeriod._meta.verbose_name, "Periodo de vuelo")
        self.assertEqual(FlightPeriod._meta.verbose_name_plural, "Periodos de vuelo")

    def test_model_ordering(self):
        """Test that model ordering is by start_date descending."""
        self.assertEqual(FlightPeriod._meta.ordering, ['-start_date'])

    def test_field_verbose_names(self):
        """Test that fields have correct verbose names."""
        start_date_field = FlightPeriod._meta.get_field('start_date')
        end_date_field = FlightPeriod._meta.get_field('end_date')
        is_active_field = FlightPeriod._meta.get_field('is_active')
        aircraft_field = FlightPeriod._meta.get_field('aircraft')
        
        self.assertEqual(start_date_field.verbose_name, "Inicio")
        self.assertEqual(end_date_field.verbose_name, "Cierre")
        self.assertEqual(is_active_field.verbose_name, "Activo")
        self.assertEqual(aircraft_field.verbose_name, "Aeronave")

    def test_field_help_texts(self):
        """Test that fields have correct help texts."""
        start_date_field = FlightPeriod._meta.get_field('start_date')
        end_date_field = FlightPeriod._meta.get_field('end_date')
        aircraft_field = FlightPeriod._meta.get_field('aircraft')
        
        self.assertEqual(start_date_field.help_text, "Inicio")
        self.assertEqual(end_date_field.help_text, "Cierre")
        self.assertEqual(aircraft_field.help_text, "Aeronave")

    def test_model_string_representation(self):
        """Test the string representation of the model."""
        period = FlightPeriod.objects.create(
            start_date=date(2025, 9, 29),
            end_date=date(2025, 10, 5),  # 7 days total (29th to 5th inclusive)
            aircraft=self.aircraft
        )
        
        expected_str = "Periodo: 2025-09-29 → 2025-10-05"
        self.assertEqual(str(period), expected_str)

    def test_period_duration_calculation(self):
        """Test period duration calculation with various lengths."""
        # Create different aircraft to avoid overlap conflicts
        aircraft1 = AircraftFactory()
        aircraft2 = AircraftFactory()
        aircraft3 = AircraftFactory()
        
        test_cases = [
            (date.today(), date.today() + timedelta(days=6), 7, aircraft1),  # 1 week (7 days)
            (date.today(), date.today() + timedelta(days=13), 14, aircraft2),  # 2 weeks (14 days)
            (date.today(), date.today() + timedelta(days=20), 21, aircraft3),  # 3 weeks (21 days)
        ]
        
        for start, end, expected_days, aircraft in test_cases:
            with self.subTest(start=start, end=end):
                period = FlightPeriod.objects.create(
                    start_date=start,
                    end_date=end,
                    aircraft=aircraft
                )
                
                actual_days = (period.end_date - period.start_date).days + 1  # +1 because it's inclusive
                self.assertEqual(actual_days, expected_days)

    def test_multiple_periods_same_aircraft(self):
        """Test that multiple periods can be created for the same aircraft."""
        period1 = FlightPeriod.objects.create(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=6),  # 7 days total
            aircraft=self.aircraft
        )
        
        period2 = FlightPeriod.objects.create(
            start_date=date.today() + timedelta(days=14),  # 2 weeks later to avoid overlap
            end_date=date.today() + timedelta(days=20),  # 7 days total
            aircraft=self.aircraft
        )
        
        # Both periods should exist
        self.assertEqual(FlightPeriod.objects.filter(aircraft=self.aircraft).count(), 2)
        
        # Both should be in the aircraft's related periods
        aircraft_periods = self.aircraft.flight_periods.all()
        self.assertIn(period1, aircraft_periods)
        self.assertIn(period2, aircraft_periods)
        
        
class FlightRequestModelTest(TestCase):
    """Test FlightRequest model methods and business logic."""

    def setUp(self):
        """Set up test data for each test."""
        # Create test aircraft
        self.aircraft = AircraftFactory()
        
        # Create test users
        self.student = UserFactory()
        self.student_profile = StudentProfileFactory(user=self.student)
        
        # Create flight period
        self.period = FlightPeriodFactory(aircraft=self.aircraft)
        
        # Generate slots
        self.period.generate_slots()
        self.slot = FlightSlot.objects.filter(flight_period=self.period).first()
        
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
        """Test that approving an already approved request raises ValidationError."""
        # Set request to approved
        self.flight_request.status = 'approved'
        self.flight_request.save()
        
        # Try to approve again
        with self.assertRaises(ValidationError) as context:
            self.flight_request.approve()
        
        self.assertIn("Solo solicitudes pendientes pueden ser aprobadas", str(context.exception))

    def test_approve_cancelled_request(self):
        """Test that approving a cancelled request raises ValidationError."""
        # Set request to cancelled
        self.flight_request.status = 'cancelled'
        self.flight_request.save()
        
        # Try to approve
        with self.assertRaises(ValidationError) as context:
            self.flight_request.approve()
        
        self.assertIn("Solo solicitudes pendientes pueden ser aprobadas", str(context.exception))

    def test_approve_slot_already_reserved(self):
        """Test that approving a request for an already reserved slot raises SlotNotAvailableError."""
        # Reserve the slot
        self.slot.status = 'reserved'
        self.slot.student = UserFactory()
        self.slot.save()
        
        # Try to approve request for reserved slot
        with self.assertRaises(SlotNotAvailableError) as context:
            self.flight_request.approve()
        
        self.assertIn("El slot ya está reservado", str(context.exception))

    def test_approve_insufficient_balance(self):
        """Test that approving a request with insufficient balance raises InsufficientBalanceError."""
        # Set student balance below minimum
        self.student_profile.balance = 400.00
        self.student_profile.save()
        
        # Try to approve
        with self.assertRaises(InsufficientBalanceError) as context:
            self.flight_request.approve()
        
        self.assertIn("Balance insuficiente para aprobar", str(context.exception))

    def test_approve_missing_student_profile(self):
        """Test that approving a request when student has no profile raises ValidationError."""
        # Delete student profile
        self.student_profile.delete()
        # Refresh the user from database to clear cached relationships
        self.student.refresh_from_db()

        # Try to approve
        with self.assertRaises(ValidationError) as context:
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

    def test_clean_method_validation(self):
        # TODO: clearn this test. Is a mess.
        """Test that the clean method properly validates FlightRequest data."""
        from scheduler.exceptions import InsufficientBalanceError, MaxRequestsExceededError
        
        # Test 1: Insufficient balance
        self.student_profile.balance = 499.99
        self.student_profile.save()
        with self.assertRaises(InsufficientBalanceError) as context:
            request = FlightRequest(
                student=self.student,
                slot=self.slot,
                status='pending'
            )
            request.full_clean()
        self.assertIn("Balance insuficiente", str(context.exception))
        
        # Test 2: Max requests exceeded
        self.student_profile.balance = 1000.00  # Allows 2 requests
        self.student_profile.save()
        
        # Create another approved request to reach the limit
        # Use the 'M' block slot that was already generated
        other_slot = FlightSlot.objects.get(
            flight_period=self.period,
            date=self.period.start_date,
            block='M',
            aircraft=self.period.aircraft
        )
        other_request = FlightRequest.objects.create(
            student=self.student,
            slot=other_slot,
            status='approved'
        )
        with self.assertRaises(MaxRequestsExceededError) as context:
            request = FlightRequest(
                student=self.student,
                slot=self.slot,
                status='pending'
            )
            request.full_clean()
        self.assertIn("Ya tiene el máximo de", str(context.exception))
        
        # Test 4: Valid request should pass
        other_request.delete()  # Remove the other request
        self.student_profile.balance = 1000.00
        self.student_profile.save()
        
        request = FlightRequest(
            student=self.student,
            slot=self.slot,
            status='pending'
        )
        # Should not raise any exception
        request.full_clean()

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
                    self.slot.refresh_from_db()
                    
                    # Verify request was approved
                    self.assertEqual(self.flight_request.status, 'approved')
                    # Verify slot was reserved and student assigned
                    self.assertEqual(self.slot.status, 'reserved')
                    self.assertEqual(self.slot.student, self.student)
                else:
                    # Should fail
                    with self.assertRaises(InsufficientBalanceError) as context:
                        self.flight_request.approve()
                    self.assertIn("Balance insuficiente para aprobar", str(context.exception))

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
        """Test that cancelling an already cancelled request raises ValidationError."""
        # Set request to cancelled
        self.flight_request.status = 'cancelled'
        self.flight_request.save()
        
        # Try to cancel again
        with self.assertRaises(ValidationError) as context:
            self.flight_request.cancel()
        
        self.assertIn("Solo solicitudes pendientes o aprobadas pueden ser canceladas", str(context.exception))

    def test_cancel_with_invalid_status(self):
        """Test that cancelling a request with invalid status raises ValidationError."""
        # Test with a non-existent status - this should fail at save time
        with self.assertRaises(ValidationError) as context:
            self.flight_request.status = 'invalid_status'
            self.flight_request.save()
        
        self.assertIn("no es una opción válida", str(context.exception))
        
        # Test with a valid but non-cancellable status (cancelled)
        self.flight_request.status = 'cancelled'
        self.flight_request.save()
        
        # Try to cancel
        with self.assertRaises(ValidationError) as context:
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
                    with self.assertRaises(ValidationError) as context:
                        self.flight_request.cancel()
                    self.assertIn("Solo solicitudes pendientes o aprobadas pueden ser canceladas", str(context.exception))
        
        # Test invalid status separately since it can't be saved
        with self.subTest(status='invalid', description="Should fail with invalid status"):
            with self.assertRaises(ValidationError) as context:
                self.flight_request.status = 'invalid'
                self.flight_request.save()
            self.assertIn("no es una opción válida", str(context.exception))

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

    # ===== CREATE_REQUEST METHOD TESTS =====

    def test_create_request_success(self):
        """Test successful flight request creation."""
        # Create a new active period with a different aircraft to avoid overlap
        other_aircraft = AircraftFactory()
        active_period = FlightPeriodFactory(aircraft=other_aircraft, is_active=True)
        active_period.generate_slots()
        
        # Use a slot from the active period
        new_slot = FlightSlot.objects.filter(flight_period=active_period).first()
        new_slot.status = 'available'
        new_slot.save()
        
        # Create a new FlightRequest instance and call create_request
        flight_request = FlightRequest()
        flight_request.create_request(self.student, new_slot)
        
        # Verify the request was created correctly
        self.assertEqual(flight_request.student, self.student)
        self.assertEqual(flight_request.slot, new_slot)
        self.assertEqual(flight_request.status, 'pending')
        
        # Verify slot was updated
        new_slot.refresh_from_db()
        self.assertEqual(new_slot.status, 'unavailable')
        self.assertEqual(new_slot.student, self.student)

    def test_create_request_inactive_period(self):
        """Test that creating request for inactive period raises PeriodNotActiveError."""
        # Make period inactive
        self.period.is_active = False
        self.period.save()
        
        # Try to create request
        flight_request = FlightRequest()
        with self.assertRaises(PeriodNotActiveError) as context:
            flight_request.create_request(self.student, self.slot)
        
        self.assertIn("El período de vuelo no está activo", str(context.exception))

    def test_create_request_atomic_transaction(self):
        """Test that create_request uses atomic transaction."""
        from unittest.mock import patch
        
        # Make the period active first
        self.period.is_active = True
        self.period.save()
        
        # Ensure slot is in a known state
        self.slot.status = 'available'
        self.slot.student = None
        self.slot.save()
        
        # Count initial requests
        initial_count = FlightRequest.objects.count()
        
        # Mock the slot save to raise an exception
        with patch.object(self.slot, 'save', side_effect=Exception("Database error")):
            flight_request = FlightRequest()
            with self.assertRaises(Exception):
                flight_request.create_request(self.student, self.slot)
        
        # Verify no new request was created (atomic transaction should have rolled back)
        final_count = FlightRequest.objects.count()
        self.assertEqual(final_count, initial_count, "No new FlightRequest should have been created")
        
        # Verify slot status was not changed (atomic transaction should have rolled back)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'available')
        self.assertIsNone(self.slot.student)