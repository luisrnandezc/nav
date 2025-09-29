from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from scheduler.models import FlightPeriod, FlightSlot
from .factories import *

User = get_user_model()

class FlightPeriodModelTest(TestCase):
    """Test FlightPeriod model methods and business logic."""

    def setUp(self):
        """Set up test data for each test."""
        self.aircraft = AircraftFactory()
        self.period = FlightPeriodFactory()

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
        """Test that invalid period lengths raise ValidationError."""
        # Test 5 days (not multiple of 7)
        period = FlightPeriod(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=4),
            aircraft=self.aircraft
        )
        
        with self.assertRaises(ValidationError) as context:
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
        """Test that periods shorter than 7 days raise ValidationError."""
        # Test 3 days
        period = FlightPeriod(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            aircraft=self.aircraft
        )
        
        with self.assertRaises(ValidationError) as context:
            period._check_flight_period_length_limits(period.start_date, period.end_date)
        
        self.assertIn("El período no puede ser menor a 7 días", str(context.exception))

    def test_check_flight_period_length_limits_too_long(self):
        """Test that periods longer than 21 days raise ValidationError."""
        # Test 4 weeks (28 days)
        period = FlightPeriod(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=27),
            aircraft=self.aircraft
        )
        
        with self.assertRaises(ValidationError) as context:
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
        """Test that overlapping periods raise ValidationError."""
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
        
        with self.assertRaises(ValidationError) as context:
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
        """Test that unavailable aircraft raise ValidationError."""
        # Make aircraft unavailable
        self.aircraft.is_available = False
        self.aircraft.save()
        
        with self.assertRaises(ValidationError) as context:
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