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
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=7),  # Exactly 7 days
            aircraft=self.aircraft
        )
        self.assertFalse(period.is_active)

    def test_created_at_auto_add(self):
        """Test that created_at is automatically set."""
        period = FlightPeriod.objects.create(
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=7),  # Exactly 7 days
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
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=6)  # 7 days total
        period = FlightPeriod.objects.create(
            start_date=start_date,
            end_date=end_date,
            aircraft=self.aircraft
        )
        
        expected_str = f"Periodo: {start_date} → {end_date}"
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


class FlightSlotModelTest(TestCase):
    """Test FlightSlot model methods and business logic."""

    def setUp(self):
        """Set up test data for each test."""
        self.aircraft = AircraftFactory()
        self.period = FlightPeriodFactory(aircraft=self.aircraft)
        self.slot = FlightSlotFactory(
            flight_period=self.period,
            aircraft=self.aircraft
        )

    # ===== BASIC MODEL TESTS =====

    def test_str_representation(self):
        """Test that the __str__ method returns the correct string."""
        expected_str = f"{self.slot.date} - {self.aircraft.registration} (Disponible) - Bloque AM"
        self.assertEqual(str(self.slot), expected_str)

    def test_str_representation_without_aircraft(self):
        """Test __str__ method when aircraft is None."""
        self.slot.aircraft = None
        self.slot.save()
        expected_str = f"{self.slot.date} - Sin aeronave (Disponible) - Bloque AM"
        self.assertEqual(str(self.slot), expected_str)

    def test_model_meta_ordering(self):
        """Test that the model is ordered by date, block, aircraft."""
        # Create multiple slots with different dates and blocks
        aircraft2 = AircraftFactory()
        period2 = FlightPeriodFactory(aircraft=aircraft2)
        
        # Create slots with specific ordering to test
        slot1 = FlightSlotFactory(
            flight_period=self.period,
            date=date.today(),
            block='M',  # Different block to avoid conflict with setUp slot
            aircraft=self.aircraft
        )
        slot2 = FlightSlotFactory(
            flight_period=period2,
            date=date.today(),
            block='AM',  # Different aircraft, so AM is fine
            aircraft=aircraft2
        )
        slot3 = FlightSlotFactory(
            flight_period=self.period,
            date=date.today() + timedelta(days=1),
            block='AM',  # Different date, so AM is fine
            aircraft=self.aircraft
        )
        
        # Query all slots - should be ordered by date, block, aircraft
        slots = list(FlightSlot.objects.all())
        
        # Find our specific slots in the ordered results
        slot1_index = slots.index(slot1)
        slot2_index = slots.index(slot2)
        slot3_index = slots.index(slot3)
        setUp_slot_index = slots.index(self.slot)
        
        # Expected ordering: date (asc), block (asc), aircraft (asc)
        # So for same date: AM before M, and for same block: aircraft1 before aircraft2
        # Expected order: setUp_slot (today, AM, aircraft1), slot2 (today, AM, aircraft2), slot1 (today, M, aircraft1), slot3 (tomorrow, AM, aircraft1)
        
        # Verify setUp_slot comes before slot2 (same date, same block, but aircraft1 < aircraft2)
        self.assertLess(setUp_slot_index, slot2_index)
        
        # Verify slot2 comes before slot1 (same date, but AM < M)
        self.assertLess(slot2_index, slot1_index)
        
        # Verify slot1 comes before slot3 (today < tomorrow)
        self.assertLess(slot1_index, slot3_index)

    def test_model_verbose_names(self):
        """Test that model has correct verbose names."""
        self.assertEqual(FlightSlot._meta.verbose_name, "Slot de vuelo")
        self.assertEqual(FlightSlot._meta.verbose_name_plural, "Slots de vuelo")

    def test_model_ordering(self):
        """Test that model ordering is by date, block, aircraft."""
        self.assertEqual(FlightSlot._meta.ordering, ['date', 'block', 'aircraft'])

    # ===== FIELD TESTS =====

    def test_field_verbose_names(self):
        """Test that fields have correct verbose names."""
        flight_period_field = FlightSlot._meta.get_field('flight_period')
        date_field = FlightSlot._meta.get_field('date')
        block_field = FlightSlot._meta.get_field('block')
        instructor_field = FlightSlot._meta.get_field('instructor')
        student_field = FlightSlot._meta.get_field('student')
        aircraft_field = FlightSlot._meta.get_field('aircraft')
        status_field = FlightSlot._meta.get_field('status')
        
        self.assertEqual(flight_period_field.verbose_name, "Periodo de vuelo")
        self.assertEqual(date_field.verbose_name, "Fecha")
        self.assertEqual(block_field.verbose_name, "Bloque")
        self.assertEqual(instructor_field.verbose_name, "Instructor")
        self.assertEqual(student_field.verbose_name, "Estudiante")
        self.assertEqual(aircraft_field.verbose_name, "Aeronave")
        self.assertEqual(status_field.verbose_name, "Estatus")

    def test_field_help_texts(self):
        """Test that fields have correct help texts."""
        flight_period_field = FlightSlot._meta.get_field('flight_period')
        date_field = FlightSlot._meta.get_field('date')
        block_field = FlightSlot._meta.get_field('block')
        instructor_field = FlightSlot._meta.get_field('instructor')
        student_field = FlightSlot._meta.get_field('student')
        aircraft_field = FlightSlot._meta.get_field('aircraft')
        status_field = FlightSlot._meta.get_field('status')
        
        self.assertEqual(flight_period_field.help_text, "Periodo de vuelo del slot")
        self.assertEqual(date_field.help_text, "Fecha del slot")
        self.assertEqual(block_field.help_text, "Bloque del slot")
        self.assertEqual(instructor_field.help_text, "Instructor del slot")
        self.assertEqual(student_field.help_text, "Estudiante del slot")
        self.assertEqual(aircraft_field.help_text, "Aeronave del slot")
        self.assertEqual(status_field.help_text, "Estatus del slot")

    def test_field_choices(self):
        """Test that fields have correct choices."""
        block_field = FlightSlot._meta.get_field('block')
        status_field = FlightSlot._meta.get_field('status')
        
        expected_block_choices = [('AM', 'AM'), ('M', 'M'), ('PM', 'PM')]
        expected_status_choices = [
            ('available', 'Disponible'),
            ('reserved', 'Reservado'),
            ('unavailable', 'No disponible')
        ]
        
        self.assertEqual(block_field.choices, expected_block_choices)
        self.assertEqual(status_field.choices, expected_status_choices)

    def test_field_max_lengths(self):
        """Test that fields have correct max lengths."""
        block_field = FlightSlot._meta.get_field('block')
        status_field = FlightSlot._meta.get_field('status')
        
        self.assertEqual(block_field.max_length, 2)
        self.assertEqual(status_field.max_length, 15)

    def test_field_defaults(self):
        """Test that fields have correct default values."""
        date_field = FlightSlot._meta.get_field('date')
        status_field = FlightSlot._meta.get_field('status')
        
        # date field has default=timezone.now
        self.assertIsNotNone(date_field.default)
        self.assertEqual(status_field.default, 'available')

    def test_field_null_blank_settings(self):
        """Test that fields have correct null and blank settings."""
        instructor_field = FlightSlot._meta.get_field('instructor')
        student_field = FlightSlot._meta.get_field('student')
        aircraft_field = FlightSlot._meta.get_field('aircraft')
        status_field = FlightSlot._meta.get_field('status')
        
        self.assertTrue(instructor_field.null)
        self.assertTrue(instructor_field.blank)
        self.assertTrue(student_field.null)
        self.assertTrue(student_field.blank)
        self.assertTrue(aircraft_field.null)
        self.assertTrue(aircraft_field.blank)
        self.assertFalse(status_field.null)
        self.assertFalse(status_field.blank)

    # ===== UNIQUE CONSTRAINT TESTS =====

    def test_unique_together_constraint(self):
        """Test that unique_together constraint works correctly."""
        # Create first slot with different block to avoid conflict with setUp slot
        slot1 = FlightSlotFactory(
            flight_period=self.period,
            date=date.today(),
            block='M',
            aircraft=self.aircraft
        )
        
        # Try to create duplicate slot (same date, block, aircraft)
        with self.assertRaises(ValidationError):
            slot2 = FlightSlot(
                flight_period=self.period,
                date=date.today(),
                block='M',
                aircraft=self.aircraft,
                status='available'
            )
            slot2.full_clean()
            slot2.save()

    def test_unique_together_allows_different_aircraft(self):
        """Test that unique_together allows same date/block with different aircraft."""
        aircraft2 = AircraftFactory()
        
        slot1 = FlightSlot.objects.create(
            flight_period=self.period,
            date=date.today(),
            block='M',  # Different block to avoid conflict with setUp slot
            aircraft=self.aircraft,
            status='available'
        )
        
        # Should be able to create slot with different aircraft
        slot2 = FlightSlot.objects.create(
            flight_period=self.period,
            date=date.today(),
            block='M',  # Same block as slot1, but different aircraft
            aircraft=aircraft2,
            status='available'
        )
        
        self.assertNotEqual(slot1.id, slot2.id)

    def test_unique_together_allows_different_blocks(self):
        """Test that unique_together allows same date/aircraft with different blocks."""
        slot1 = FlightSlot.objects.create(
            flight_period=self.period,
            date=date.today(),
            block='M',  # Different block to avoid conflict with setUp slot
            aircraft=self.aircraft,
            status='available'
        )
        
        # Should be able to create slot with different block
        slot2 = FlightSlot.objects.create(
            flight_period=self.period,
            date=date.today(),
            block='PM',  # Different block from slot1
            aircraft=self.aircraft,
            status='available'
        )
        
        self.assertNotEqual(slot1.id, slot2.id)

    def test_unique_together_allows_different_dates(self):
        """Test that unique_together allows same block/aircraft with different dates."""
        slot1 = FlightSlot.objects.create(
            flight_period=self.period,
            date=date.today(),
            block='M',  # Different block to avoid conflict with setUp slot
            aircraft=self.aircraft,
            status='available'
        )
        
        # Should be able to create slot with different date
        slot2 = FlightSlot.objects.create(
            flight_period=self.period,
            date=date.today() + timedelta(days=1),
            block='M',  # Same block as slot1, but different date
            aircraft=self.aircraft,
            status='available'
        )
        
        self.assertNotEqual(slot1.id, slot2.id)

    # ===== FOREIGN KEY RELATIONSHIP TESTS =====

    def test_flight_period_foreign_key_relationship(self):
        """Test the foreign key relationship with FlightPeriod."""
        # Test forward relationship
        self.assertEqual(self.slot.flight_period, self.period)
        
        # Test reverse relationship
        period_slots = self.period.slots.all()
        self.assertIn(self.slot, period_slots)

    def test_flight_period_cascade_delete(self):
        """Test that deleting flight period cascades to flight slots."""
        slot_id = self.slot.id
        self.period.delete()
        
        # Slot should be deleted due to CASCADE
        with self.assertRaises(FlightSlot.DoesNotExist):
            FlightSlot.objects.get(id=slot_id)

    def test_aircraft_foreign_key_relationship(self):
        """Test the foreign key relationship with Aircraft."""
        # Test forward relationship
        self.assertEqual(self.slot.aircraft, self.aircraft)
        
        # Test reverse relationship
        aircraft_slots = self.aircraft.flight_slots.all()
        self.assertIn(self.slot, aircraft_slots)

    def test_aircraft_cascade_delete(self):
        """Test that deleting aircraft cascades to delete flight period and slots."""
        slot_id = self.slot.id
        self.aircraft.delete()
        
        # Slot should be deleted due to CASCADE chain: Aircraft -> FlightPeriod -> FlightSlot
        with self.assertRaises(FlightSlot.DoesNotExist):
            FlightSlot.objects.get(id=slot_id)

    def test_aircraft_set_null_on_delete_direct_assignment(self):
        """Test that deleting aircraft sets slot aircraft to NULL when directly assigned."""
        # Create a slot with a different aircraft that's not tied to the flight period
        other_aircraft = AircraftFactory()
        slot = FlightSlot.objects.create(
            flight_period=self.period,
            date=date.today(),
            block='PM',
            aircraft=other_aircraft,
            status='available'
        )
        
        # Delete the other aircraft (which has no flight periods, so no cascade)
        other_aircraft.delete()
        
        # Slot should still exist but aircraft should be None (SET_NULL behavior)
        slot.refresh_from_db()
        self.assertIsNone(slot.aircraft)
        # Verify the slot still exists and has its flight_period intact
        self.assertEqual(slot.flight_period, self.period)

    def test_aircraft_cascade_delete_with_flight_periods(self):
        """Test that deleting aircraft with flight periods cascades to delete slots."""
        # Create an aircraft with its own flight period and slot
        other_aircraft = AircraftFactory()
        other_period = FlightPeriodFactory(aircraft=other_aircraft)
        other_slot = FlightSlotFactory(
            flight_period=other_period,
            aircraft=other_aircraft
        )
        
        # Delete the aircraft - this should cascade delete the period and slot
        other_aircraft.delete()
        
        # Both the period and slot should be deleted
        with self.assertRaises(FlightPeriod.DoesNotExist):
            FlightPeriod.objects.get(id=other_period.id)
        
        with self.assertRaises(FlightSlot.DoesNotExist):
            FlightSlot.objects.get(id=other_slot.id)

    def test_instructor_foreign_key_relationship(self):
        """Test the foreign key relationship with User (instructor)."""
        instructor = UserFactory(role='INSTRUCTOR')
        self.slot.instructor = instructor
        self.slot.save()
        
        # Test forward relationship
        self.assertEqual(self.slot.instructor, instructor)
        
        # Test reverse relationship
        instructor_slots = instructor.instructor_flight_slots.all()
        self.assertIn(self.slot, instructor_slots)

    def test_instructor_set_null_on_delete(self):
        """Test that deleting instructor sets slot instructor to NULL."""
        instructor = UserFactory(role='INSTRUCTOR')
        self.slot.instructor = instructor
        self.slot.save()
        
        instructor.delete()
        
        # Slot should still exist but instructor should be None
        self.slot.refresh_from_db()
        self.assertIsNone(self.slot.instructor)

    def test_student_foreign_key_relationship(self):
        """Test the foreign key relationship with User (student)."""
        student = UserFactory(role='STUDENT')
        self.slot.student = student
        self.slot.save()
        
        # Test forward relationship
        self.assertEqual(self.slot.student, student)
        
        # Test reverse relationship
        student_slots = student.student_flight_slots.all()
        self.assertIn(self.slot, student_slots)

    def test_student_set_null_on_delete(self):
        """Test that deleting student sets slot student to NULL."""
        student = UserFactory(role='STUDENT')
        self.slot.student = student
        self.slot.save()
        
        student.delete()
        
        # Slot should still exist but student should be None
        self.slot.refresh_from_db()
        self.assertIsNone(self.slot.student)

    # ===== CHOICE FIELD TESTS =====

    def test_block_choices_validation(self):
        """Test that block field validates against valid choices."""
        valid_blocks = ['AM', 'M', 'PM']
        
        for block in valid_blocks:
            with self.subTest(block=block):
                self.slot.block = block
                self.slot.full_clean()  # Should not raise exception

    def test_block_choices_invalid_choice(self):
        """Test that block field raises ValidationError for invalid choices."""
        with self.assertRaises(ValidationError) as context:
            self.slot.block = 'INVALID'
            self.slot.full_clean()
        
        self.assertIn("no es una opción válida", str(context.exception))

    def test_status_choices_validation(self):
        """Test that status field validates against valid choices."""
        valid_statuses = ['available', 'reserved', 'unavailable']
        
        for status in valid_statuses:
            with self.subTest(status=status):
                self.slot.status = status
                self.slot.full_clean()  # Should not raise exception

    def test_status_choices_invalid_choice(self):
        """Test that status field raises ValidationError for invalid choices."""
        with self.assertRaises(ValidationError) as context:
            self.slot.status = 'INVALID'
            self.slot.full_clean()
        
        self.assertIn("no es una opción válida", str(context.exception))

    def test_get_block_display(self):
        """Test that get_block_display returns correct display value."""
        self.slot.block = 'AM'
        self.assertEqual(self.slot.get_block_display(), 'AM')
        
        self.slot.block = 'M'
        self.assertEqual(self.slot.get_block_display(), 'M')
        
        self.slot.block = 'PM'
        self.assertEqual(self.slot.get_block_display(), 'PM')

    def test_get_status_display(self):
        """Test that get_status_display returns correct display value."""
        self.slot.status = 'available'
        self.assertEqual(self.slot.get_status_display(), 'Disponible')
        
        self.slot.status = 'reserved'
        self.assertEqual(self.slot.get_status_display(), 'Reservado')
        
        self.slot.status = 'unavailable'
        self.assertEqual(self.slot.get_status_display(), 'No disponible')

    # ===== LIMIT_CHOICES_TO TESTS =====

    def test_instructor_limit_choices_to(self):
        """Test that instructor field limits choices to INSTRUCTOR role."""
        # Create users with different roles
        instructor = UserFactory(role='INSTRUCTOR')
        student = UserFactory(role='STUDENT')
        staff = UserFactory(role='STAFF')
        
        # Should be able to assign instructor
        self.slot.instructor = instructor
        self.slot.full_clean()  # Should not raise exception
        
        # Should not be able to assign student
        with self.assertRaises(ValidationError):
            self.slot.instructor = student
            self.slot.full_clean()
        
        # Should not be able to assign staff
        with self.assertRaises(ValidationError):
            self.slot.instructor = staff
            self.slot.full_clean()

    def test_student_limit_choices_to(self):
        """Test that student field limits choices to STUDENT role."""
        # Create users with different roles
        student = UserFactory(role='STUDENT')
        instructor = UserFactory(role='INSTRUCTOR')
        staff = UserFactory(role='STAFF')
        
        # Should be able to assign student
        self.slot.student = student
        self.slot.full_clean()  # Should not raise exception
        
        # Should not be able to assign instructor
        with self.assertRaises(ValidationError):
            self.slot.student = instructor
            self.slot.full_clean()
        
        # Should not be able to assign staff
        with self.assertRaises(ValidationError):
            self.slot.student = staff
            self.slot.full_clean()

    def test_aircraft_limit_choices_to(self):
        """Test that aircraft field limits choices to active and available aircraft."""
        # Create aircraft with different availability states
        active_available = AircraftFactory(is_active=True, is_available=True)
        active_unavailable = AircraftFactory(is_active=True, is_available=False)
        inactive_available = AircraftFactory(is_active=False, is_available=True)
        inactive_unavailable = AircraftFactory(is_active=False, is_available=False)
        
        # Should be able to assign active and available aircraft
        self.slot.aircraft = active_available
        self.slot.full_clean()  # Should not raise exception
        
        # Should not be able to assign active but unavailable aircraft
        with self.assertRaises(ValidationError):
            self.slot.aircraft = active_unavailable
            self.slot.full_clean()
        
        # Should not be able to assign inactive but available aircraft
        with self.assertRaises(ValidationError):
            self.slot.aircraft = inactive_available
            self.slot.full_clean()
        
        # Should not be able to assign inactive and unavailable aircraft
        with self.assertRaises(ValidationError):
            self.slot.aircraft = inactive_unavailable
            self.slot.full_clean()

    # ===== DATE FIELD TESTS =====

    def test_date_field_default(self):
        """Test that date field uses timezone.now as default."""
        # Create slot without specifying date (use different block to avoid unique constraint)
        slot = FlightSlot.objects.create(
            flight_period=self.period,
            block='M',  # Different block to avoid conflict with setUp slot
            aircraft=self.aircraft,
            status='available'
        )
        
        # Date should be set to current date
        self.assertEqual(slot.date, date.today())

    def test_date_field_can_be_set(self):
        """Test that date field can be set to specific date."""
        specific_date = date.today() + timedelta(days=5)
        self.slot.date = specific_date
        self.slot.save()
        
        self.assertEqual(self.slot.date, specific_date)

    def test_date_field_future_date(self):
        """Test that date field can be set to future date."""
        future_date = date.today() + timedelta(days=30)
        self.slot.date = future_date
        self.slot.full_clean()  # Should not raise exception

    def test_date_field_past_date(self):
        """Test that date field can be set to past date."""
        past_date = date.today() - timedelta(days=30)
        self.slot.date = past_date
        self.slot.full_clean()  # Should not raise exception

    # ===== STATUS TRANSITION TESTS =====

    def test_status_available_to_reserved(self):
        """Test transitioning from available to reserved status."""
        self.assertEqual(self.slot.status, 'available')
        
        self.slot.status = 'reserved'
        self.slot.student = UserFactory(role='STUDENT')
        self.slot.save()
        
        self.assertEqual(self.slot.status, 'reserved')
        self.assertIsNotNone(self.slot.student)

    def test_status_available_to_unavailable(self):
        """Test transitioning from available to unavailable status."""
        self.assertEqual(self.slot.status, 'available')
        
        self.slot.status = 'unavailable'
        self.slot.save()
        
        self.assertEqual(self.slot.status, 'unavailable')

    def test_status_reserved_to_available(self):
        """Test transitioning from reserved to available status."""
        self.slot.status = 'reserved'
        self.slot.student = UserFactory(role='STUDENT')
        self.slot.save()
        
        self.slot.status = 'available'
        self.slot.student = None
        self.slot.save()
        
        self.assertEqual(self.slot.status, 'available')
        self.assertIsNone(self.slot.student)

    def test_status_unavailable_to_available(self):
        """Test transitioning from unavailable to available status."""
        self.slot.status = 'unavailable'
        self.slot.save()
        
        self.slot.status = 'available'
        self.slot.save()
        
        self.assertEqual(self.slot.status, 'available')

    # ===== EDGE CASES AND ERROR CONDITIONS =====

    def test_slot_without_aircraft(self):
        """Test slot behavior when aircraft is None."""
        self.slot.aircraft = None
        self.slot.save()
        
        # Should still be able to save
        self.assertIsNone(self.slot.aircraft)
        
        # String representation should handle None aircraft
        expected_str = f"{self.slot.date} - Sin aeronave (Disponible) - Bloque AM"
        self.assertEqual(str(self.slot), expected_str)

    def test_slot_without_instructor(self):
        """Test slot behavior when instructor is None."""
        self.slot.instructor = None
        self.slot.save()
        
        # Should still be able to save
        self.assertIsNone(self.slot.instructor)

    def test_slot_without_student(self):
        """Test slot behavior when student is None."""
        self.slot.student = None
        self.slot.save()
        
        # Should still be able to save
        self.assertIsNone(self.slot.student)

    def test_slot_with_all_relationships(self):
        """Test slot with all relationships populated."""
        instructor = UserFactory(role='INSTRUCTOR')
        student = UserFactory(role='STUDENT')
        
        self.slot.instructor = instructor
        self.slot.student = student
        self.slot.status = 'reserved'
        self.slot.save()
        
        self.assertEqual(self.slot.instructor, instructor)
        self.assertEqual(self.slot.student, student)
        self.assertEqual(self.slot.status, 'reserved')

    def test_slot_creation_with_minimal_data(self):
        """Test creating slot with only required fields."""
        slot = FlightSlot.objects.create(
            flight_period=self.period,
            block='PM',
            aircraft=self.aircraft
        )
        
        self.assertEqual(slot.flight_period, self.period)
        self.assertEqual(slot.block, 'PM')
        self.assertEqual(slot.aircraft, self.aircraft)
        self.assertEqual(slot.status, 'available')
        self.assertIsNone(slot.instructor)
        self.assertIsNone(slot.student)
        self.assertEqual(slot.date, date.today())

    def test_slot_creation_with_all_fields(self):
        """Test creating slot with all fields populated."""
        instructor = UserFactory(role='INSTRUCTOR')
        student = UserFactory(role='STUDENT')
        specific_date = date.today() + timedelta(days=3)
        
        slot = FlightSlot.objects.create(
            flight_period=self.period,
            date=specific_date,
            block='M',
            instructor=instructor,
            student=student,
            aircraft=self.aircraft,
            status='reserved'
        )
        
        self.assertEqual(slot.flight_period, self.period)
        self.assertEqual(slot.date, specific_date)
        self.assertEqual(slot.block, 'M')
        self.assertEqual(slot.instructor, instructor)
        self.assertEqual(slot.student, student)
        self.assertEqual(slot.aircraft, self.aircraft)
        self.assertEqual(slot.status, 'reserved')

    # ===== QUERY TESTS =====

    def test_filter_by_status(self):
        """Test filtering slots by status."""
        # Create slots with different statuses
        available_slot = FlightSlotFactory(status='available')
        reserved_slot = FlightSlotFactory(status='reserved')
        unavailable_slot = FlightSlotFactory(status='unavailable')
        
        # Test filtering
        available_slots = FlightSlot.objects.filter(status='available')
        reserved_slots = FlightSlot.objects.filter(status='reserved')
        unavailable_slots = FlightSlot.objects.filter(status='unavailable')
        
        self.assertIn(available_slot, available_slots)
        self.assertIn(reserved_slot, reserved_slots)
        self.assertIn(unavailable_slot, unavailable_slots)
        
        self.assertNotIn(available_slot, reserved_slots)
        self.assertNotIn(available_slot, unavailable_slots)

    def test_filter_by_block(self):
        """Test filtering slots by block."""
        # Create slots with different blocks
        am_slot = FlightSlotFactory(block='AM')
        m_slot = FlightSlotFactory(block='M')
        pm_slot = FlightSlotFactory(block='PM')
        
        # Test filtering
        am_slots = FlightSlot.objects.filter(block='AM')
        m_slots = FlightSlot.objects.filter(block='M')
        pm_slots = FlightSlot.objects.filter(block='PM')
        
        self.assertIn(am_slot, am_slots)
        self.assertIn(m_slot, m_slots)
        self.assertIn(pm_slot, pm_slots)

    def test_filter_by_date_range(self):
        """Test filtering slots by date range."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        # Create slots with different dates
        yesterday_slot = FlightSlotFactory(date=yesterday)
        today_slot = FlightSlotFactory(date=today)
        tomorrow_slot = FlightSlotFactory(date=tomorrow)
        
        # Test filtering
        today_slots = FlightSlot.objects.filter(date=today)
        future_slots = FlightSlot.objects.filter(date__gte=today)
        past_slots = FlightSlot.objects.filter(date__lt=today)
        
        self.assertIn(today_slot, today_slots)
        self.assertIn(today_slot, future_slots)
        self.assertIn(tomorrow_slot, future_slots)
        self.assertIn(yesterday_slot, past_slots)

    def test_filter_by_aircraft(self):
        """Test filtering slots by aircraft."""
        aircraft1 = AircraftFactory()
        aircraft2 = AircraftFactory()
        
        slot1 = FlightSlotFactory(aircraft=aircraft1)
        slot2 = FlightSlotFactory(aircraft=aircraft2)
        
        # Test filtering
        aircraft1_slots = FlightSlot.objects.filter(aircraft=aircraft1)
        aircraft2_slots = FlightSlot.objects.filter(aircraft=aircraft2)
        
        self.assertIn(slot1, aircraft1_slots)
        self.assertIn(slot2, aircraft2_slots)
        self.assertNotIn(slot1, aircraft2_slots)
        self.assertNotIn(slot2, aircraft1_slots)

    def test_filter_by_flight_period(self):
        """Test filtering slots by flight period."""
        period1 = FlightPeriodFactory()
        period2 = FlightPeriodFactory()
        
        slot1 = FlightSlotFactory(flight_period=period1)
        slot2 = FlightSlotFactory(flight_period=period2)
        
        # Test filtering
        period1_slots = FlightSlot.objects.filter(flight_period=period1)
        period2_slots = FlightSlot.objects.filter(flight_period=period2)
        
        self.assertIn(slot1, period1_slots)
        self.assertIn(slot2, period2_slots)
        self.assertNotIn(slot1, period2_slots)
        self.assertNotIn(slot2, period1_slots)

    def test_filter_by_instructor(self):
        """Test filtering slots by instructor."""
        instructor1 = UserFactory(role='INSTRUCTOR')
        instructor2 = UserFactory(role='INSTRUCTOR')
        
        slot1 = FlightSlotFactory(instructor=instructor1)
        slot2 = FlightSlotFactory(instructor=instructor2)
        
        # Test filtering
        instructor1_slots = FlightSlot.objects.filter(instructor=instructor1)
        instructor2_slots = FlightSlot.objects.filter(instructor=instructor2)
        
        self.assertIn(slot1, instructor1_slots)
        self.assertIn(slot2, instructor2_slots)
        self.assertNotIn(slot1, instructor2_slots)
        self.assertNotIn(slot2, instructor1_slots)

    def test_filter_by_student(self):
        """Test filtering slots by student."""
        student1 = UserFactory(role='STUDENT')
        student2 = UserFactory(role='STUDENT')
        
        slot1 = FlightSlotFactory(student=student1)
        slot2 = FlightSlotFactory(student=student2)
        
        # Test filtering
        student1_slots = FlightSlot.objects.filter(student=student1)
        student2_slots = FlightSlot.objects.filter(student=student2)
        
        self.assertIn(slot1, student1_slots)
        self.assertIn(slot2, student2_slots)
        self.assertNotIn(slot1, student2_slots)
        self.assertNotIn(slot2, student1_slots)

    # ===== COMPLEX QUERY TESTS =====

    def test_available_slots_query(self):
        """Test querying for available slots."""
        # Create slots with different statuses
        available_slot = FlightSlotFactory(status='available')
        reserved_slot = FlightSlotFactory(status='reserved')
        unavailable_slot = FlightSlotFactory(status='unavailable')
        
        # Query available slots
        available_slots = FlightSlot.objects.filter(status='available')
        
        self.assertIn(available_slot, available_slots)
        self.assertNotIn(reserved_slot, available_slots)
        self.assertNotIn(unavailable_slot, available_slots)

    def test_reserved_slots_query(self):
        """Test querying for reserved slots."""
        # Create slots with different statuses
        available_slot = FlightSlotFactory(status='available')
        reserved_slot = FlightSlotFactory(status='reserved')
        unavailable_slot = FlightSlotFactory(status='unavailable')
        
        # Query reserved slots
        reserved_slots = FlightSlot.objects.filter(status='reserved')
        
        self.assertIn(reserved_slot, reserved_slots)
        self.assertNotIn(available_slot, reserved_slots)
        self.assertNotIn(unavailable_slot, reserved_slots)

    def test_slots_for_specific_date(self):
        """Test querying slots for a specific date."""
        specific_date = date.today() + timedelta(days=5)
        
        # Create slots for different dates
        today_slot = FlightSlotFactory(date=date.today())
        specific_date_slot = FlightSlotFactory(date=specific_date)
        other_date_slot = FlightSlotFactory(date=specific_date + timedelta(days=1))
        
        # Query slots for specific date
        specific_date_slots = FlightSlot.objects.filter(date=specific_date)
        
        self.assertIn(specific_date_slot, specific_date_slots)
        self.assertNotIn(today_slot, specific_date_slots)
        self.assertNotIn(other_date_slot, specific_date_slots)

    def test_slots_for_specific_aircraft_and_date(self):
        """Test querying slots for specific aircraft and date."""
        specific_date = date.today() + timedelta(days=3)
        aircraft = AircraftFactory()
        
        # Create slots with different combinations
        target_slot = FlightSlotFactory(aircraft=aircraft, date=specific_date)
        different_aircraft_slot = FlightSlotFactory(aircraft=AircraftFactory(), date=specific_date)
        different_date_slot = FlightSlotFactory(aircraft=aircraft, date=specific_date + timedelta(days=1))
        
        # Query slots for specific aircraft and date
        target_slots = FlightSlot.objects.filter(aircraft=aircraft, date=specific_date)
        
        self.assertIn(target_slot, target_slots)
        self.assertNotIn(different_aircraft_slot, target_slots)
        self.assertNotIn(different_date_slot, target_slots)

    def test_slots_ordered_by_date_and_block(self):
        """Test that slots are properly ordered by date and block."""
        # Create slots with different dates and blocks
        slot1 = FlightSlotFactory(date=date.today(), block='AM')
        slot2 = FlightSlotFactory(date=date.today(), block='M')
        slot3 = FlightSlotFactory(date=date.today(), block='PM')
        slot4 = FlightSlotFactory(date=date.today() + timedelta(days=1), block='AM')
        
        # Query all slots
        slots = list(FlightSlot.objects.all())
        
        # Find our slots in the results
        slot1_index = slots.index(slot1)
        slot2_index = slots.index(slot2)
        slot3_index = slots.index(slot3)
        slot4_index = slots.index(slot4)
        
        # Should be ordered by date, then block
        self.assertLess(slot1_index, slot2_index)  # AM before M
        self.assertLess(slot2_index, slot3_index)  # M before PM
        self.assertLess(slot3_index, slot4_index)  # Today before tomorrow