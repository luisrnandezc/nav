from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from scheduler.models import FlightPeriod, FlightSlot
from .factories import *

User = get_user_model()


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