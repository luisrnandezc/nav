from django.test import TestCase
from datetime import date
from scheduler.forms import CreateFlightPeriodForm
from .factories import *


class CreateFlightPeriodFormTest(TestCase):
    """Test CreateFlightPeriodForm validation and functionality."""

    def setUp(self):
        """Set up test data for each test."""
        self.aircraft = AircraftFactory()

    def test_start_date_must_be_monday(self):
        """Test that start date validation requires Monday - test clean method directly."""
        form = CreateFlightPeriodForm()

        # Manually set cleaned_data to bypass model validation
        form.cleaned_data = {'start_date': None}
        
        form.cleaned_data['start_date'] = date(2025, 9, 28)  # Sunday
        result = form.clean_start_date()
        self.assertEqual(result, date(2025, 9, 28))
        self.assertIn('start_date', form.errors)
        self.assertIn('La fecha de inicio debe ser un lunes', str(form.errors['start_date']))

    def test_end_date_must_be_sunday(self):
        """Test that end date validation method works correctly."""
        form = CreateFlightPeriodForm()

        # Manually set cleaned_data to bypass model validation
        form.cleaned_data = {'end_date': None}
        form.cleaned_data['end_date'] = date(2025, 10, 1)  # Wednesday

        result = form.clean_end_date()
        self.assertEqual(result, date(2025, 10, 1))
        self.assertIn('end_date', form.errors)
        self.assertIn('La fecha de cierre debe ser un domingo', str(form.errors['end_date']))

    def test_end_date_must_be_after_start_date(self):
        """Test that end date must be after start date - test clean method directly."""
        form = CreateFlightPeriodForm()

        # Manually set cleaned_data to bypass model validation
        form.cleaned_data = {
            'start_date': date(2025, 9, 29),  # Monday
            'end_date': date(2025, 9, 28),    # Sunday (before start date)
        }
        
        result = form.clean()
        self.assertEqual(result, form.cleaned_data)
        self.assertIn('end_date', form.errors)
        self.assertIn('La fecha de cierre debe ser posterior a la fecha de inicio', str(form.errors['end_date']))