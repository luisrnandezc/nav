from datetime import date
from decimal import Decimal
from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from fleet.models import Aircraft
from fms.models import (
    FlightEvaluation0_100,
    FlightEvaluation100_120,
    FlightEvaluation120_170,
)
from prod.services import get_fuel_consumed


class FuelConsumptionTests(TestCase):
    def setUp(self):
        self.aircraft, _ = Aircraft.objects.get_or_create(
            registration='YV204E',
            defaults={
                'manufacturer': 'Piper',
                'model': 'PA-28',
                'serial_number': 'PROD-001',
                'year_manufactured': 1980,
            },
        )
        self.other_aircraft, _ = Aircraft.objects.get_or_create(
            registration='YV206E',
            defaults={
                'manufacturer': 'Piper',
                'model': 'PA-28',
                'serial_number': 'PROD-002',
                'year_manufactured': 1981,
            },
        )

    def create_evaluation(self, model, **overrides):
        values = {
            'student_id': 1000001,
            'student_license_type': 'PPA',
            'student_license_number': 1000001,
            'instructor_id': 2000001,
            'instructor_license_number': 2000001,
            'session_date': date(2026, 6, 10),
            'initial_hourmeter': Decimal('100.0'),
            'final_hourmeter': Decimal('101.5'),
            'session_flight_hours': Decimal('1.5'),
            'fuel_consumed': Decimal('10.0'),
            'hourly_rate_applied': Decimal('130.00'),
            'fuel_rate_applied': Decimal('4.00'),
            'aircraft': self.aircraft,
        }
        values.update(overrides)
        # Reporting tests need persisted historical rows without invoking the
        # evaluation models' accounting side effects.
        return model.objects.bulk_create([model(**values)])[0]

    def test_combines_all_evaluation_types_using_historical_fuel_rates(self):
        self.create_evaluation(FlightEvaluation0_100, fuel_consumed=Decimal('10.0'))
        self.create_evaluation(
            FlightEvaluation100_120,
            fuel_consumed=Decimal('20.0'),
            fuel_rate_applied=Decimal('3.50'),
            session_flight_hours=Decimal('2.0'),
        )
        self.create_evaluation(
            FlightEvaluation120_170,
            fuel_consumed=Decimal('5.0'),
            fuel_rate_applied=Decimal('5.00'),
            session_flight_hours=Decimal('1.0'),
        )
        self.aircraft.fuel_cost = Decimal('9.00')
        self.aircraft.save(update_fields=['fuel_cost'])

        report = get_fuel_consumed(
            start_date=date(2026, 6, 10),
            end_date=date(2026, 8, 12),
        )

        self.assertEqual(report.evaluation_count, 3)
        self.assertEqual(report.flight_hours, Decimal('4.5'))
        self.assertEqual(report.fuel_liters, Decimal('35.0'))
        self.assertEqual(report.fuel_cost_usd, Decimal('135.00'))

    def test_filters_inclusive_dates_aircraft_and_evaluation_types(self):
        self.create_evaluation(FlightEvaluation0_100)
        self.create_evaluation(
            FlightEvaluation0_100,
            session_date=date(2026, 8, 12),
            fuel_consumed=Decimal('7.0'),
        )
        self.create_evaluation(
            FlightEvaluation0_100,
            session_date=date(2026, 8, 13),
            fuel_consumed=Decimal('99.0'),
        )
        self.create_evaluation(
            FlightEvaluation0_100,
            aircraft=self.other_aircraft,
            fuel_consumed=Decimal('99.0'),
        )
        self.create_evaluation(FlightEvaluation100_120, fuel_consumed=Decimal('99.0'))

        report = get_fuel_consumed(
            start_date=date(2026, 6, 10),
            end_date=date(2026, 8, 12),
            evaluation_types=['0-100'],
            aircraft_registration='yv204e',
        )

        self.assertEqual(report.evaluation_count, 2)
        self.assertEqual(report.fuel_liters, Decimal('17.0'))
        self.assertEqual(report.aircraft, 'YV204E')

    def test_rejects_invalid_input(self):
        with self.assertRaises(ValidationError):
            get_fuel_consumed(
                start_date=date(2026, 8, 12),
                end_date=date(2026, 6, 10),
            )
        with self.assertRaises(ValidationError):
            get_fuel_consumed(
                start_date=date(2026, 6, 10),
                end_date=date(2026, 8, 12),
                aircraft_registration='UNKNOWN',
            )

    def test_management_command_prints_report(self):
        self.create_evaluation(FlightEvaluation0_100)
        stdout = StringIO()

        call_command(
            'fuel_consumed',
            start='2026-06-10',
            end='2026-08-12',
            evaluations=['0-100'],
            aircraft='YV204E',
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn('Evaluation count: 1', output)
        self.assertIn('Fuel consumed: 10.0 L', output)
        self.assertIn('Fuel cost: $40.00 USD', output)

    def test_management_command_rejects_bad_date(self):
        with self.assertRaises(CommandError):
            call_command(
                'fuel_consumed',
                start='10-06-2026',
                end='2026-08-12',
            )
