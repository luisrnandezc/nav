from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from fleet.models import Aircraft, Simulator
from fms.models import ExternalFlightEvaluation, FlightEvaluation0_100, FlightReport, SimEvaluation
from prod.services import ProductionFilters, get_production_report


class ProductionReportTests(TestCase):
    def setUp(self):
        self.aircraft, _ = Aircraft.objects.get_or_create(
            registration='YV204E',
            defaults={
                'manufacturer': 'Piper',
                'model': 'PA-28',
                'serial_number': 'PRODUCTION-001',
                'year_manufactured': 1980,
            },
        )
        self.simulator, _ = Simulator.objects.get_or_create(name='FPT')

    def create_flight(self, **overrides):
        values = {
            'student_id': 1000001,
            'student_first_name': 'Ana',
            'student_last_name': 'Alumno',
            'student_license_type': 'PPA',
            'student_license_number': 1000001,
            'instructor_id': 2000001,
            'instructor_first_name': 'Iván',
            'instructor_last_name': 'Instructor',
            'instructor_license_number': 2000001,
            'session_date': date(2026, 6, 10),
            'session_flight_hours': Decimal('2.0'),
            'fuel_consumed': Decimal('20.0'),
            'hourly_rate_applied': Decimal('125.00'),
            'aircraft_rate_applied': Decimal('130.00'),
            'instructor_rate_applied': Decimal('20.00'),
            'fuel_rate_applied': Decimal('3.11'),
            'aircraft': self.aircraft,
        }
        values.update(overrides)
        return FlightEvaluation0_100.objects.bulk_create(
            [FlightEvaluation0_100(**values)]
        )[0]

    def create_sim(self, **overrides):
        values = {
            'student_id': 1000001,
            'student_first_name': 'Ana',
            'student_last_name': 'Alumno',
            'student_license_type': 'PPA',
            'student_license_number': 1000001,
            'instructor_id': 2000001,
            'instructor_first_name': 'Iván',
            'instructor_last_name': 'Instructor',
            'instructor_license_number': 2000001,
            'session_date': date(2026, 6, 10),
            'session_sim_hours': Decimal('2.0'),
            'simulator_rate_applied': Decimal('35.00'),
            'instructor_rate_applied': Decimal('15.00'),
            'simulator': self.simulator,
        }
        values.update(overrides)
        return SimEvaluation.objects.bulk_create([SimEvaluation(**values)])[0]

    def create_external(self, **overrides):
        values = {
            'instructor_id': 2000001,
            'instructor_first_name': 'Iván',
            'instructor_last_name': 'Instructor',
            'instructor_license_number': 2000001,
            'student_id': 1000001,
            'student_first_name': 'Ana',
            'student_last_name': 'Alumno',
            'student_license_type': 'PPA',
            'student_license_number': 1000001,
            'evaluation_type': 'OTRO',
            'session_date': date(2026, 6, 10),
            'fuel_consumed': Decimal('5.0'),
            'fuel_rate_applied': Decimal('3.11'),
            'aircraft_registration': 'N123EX',
        }
        values.update(overrides)
        return ExternalFlightEvaluation.objects.bulk_create(
            [ExternalFlightEvaluation(**values)]
        )[0]

    def create_flight_report(self, **overrides):
        values = {
            'pilot_id': 3000001,
            'pilot_license_number': 3000001,
            'flight_date': date(2026, 6, 10),
            'fuel_consumed': Decimal('3.0'),
            'fuel_rate_applied': Decimal('3.11'),
            'aircraft': self.aircraft,
        }
        values.update(overrides)
        return FlightReport.objects.bulk_create([FlightReport(**values)])[0]

    def test_report_calculates_internal_flight_and_simulator_totals(self):
        self.create_flight()
        self.create_sim()
        self.create_external()
        self.create_flight_report()

        report = get_production_report(
            ProductionFilters(date(2026, 6, 5), date(2026, 8, 13))
        )

        self.assertEqual(report.totals.flight_hours, Decimal('2.0'))
        self.assertEqual(report.totals.gross_flying_income_usd, Decimal('260.00'))
        self.assertEqual(report.totals.instructor_flying_cost_usd, Decimal('40.00'))
        self.assertEqual(report.totals.net_flying_revenue_usd, Decimal('220.00'))
        self.assertEqual(report.totals.student_flying_value_usd, Decimal('250.00'))
        self.assertEqual(report.totals.simulator_hours, Decimal('2.0'))
        self.assertEqual(report.totals.gross_simulator_income_usd, Decimal('70.00'))
        self.assertEqual(report.totals.instructor_simulator_cost_usd, Decimal('30.00'))
        self.assertEqual(report.totals.net_simulator_revenue_usd, Decimal('40.00'))
        self.assertEqual(report.totals.instructor_production_usd, Decimal('70.00'))
        self.assertEqual(report.totals.fuel_liters, Decimal('20.0'))
        self.assertEqual(report.totals.fuel_cost_usd, Decimal('62.20'))
        self.assertEqual(
            report.totals.operating_flying_profit_usd,
            Decimal('157.80'),
        )

    def test_external_evaluations_and_reports_are_ignored(self):
        self.create_external(fuel_consumed=Decimal('7.0'))
        self.create_flight_report(fuel_consumed=Decimal('4.0'))

        report = get_production_report(
            ProductionFilters(date(2026, 6, 5), date(2026, 8, 13))
        )

        self.assertEqual(report.totals.fuel_liters, ZERO)
        self.assertEqual(report.totals.fuel_cost_usd, ZERO)
        self.assertEqual(report.totals.flight_hours, ZERO)
        self.assertEqual(report.totals.gross_flying_income_usd, ZERO)
        self.assertEqual(report.totals.instructor_production_usd, ZERO)

    def test_report_produces_each_required_breakdown(self):
        self.create_flight()
        self.create_sim()
        self.create_external()

        report = get_production_report(
            ProductionFilters(date(2026, 6, 5), date(2026, 8, 13))
        )

        self.assertEqual({row.key for row in report.by_aircraft}, {'YV204E'})
        self.assertEqual([row.label for row in report.by_simulator], ['FPT'])
        self.assertEqual([row.key for row in report.by_instructor], ['2000001'])
        self.assertEqual([row.key for row in report.by_student], ['1000001'])
        self.assertEqual(report.flight_trend.grouping, 'monthly')
        self.assertEqual(report.flight_trend.labels, ['06/2026', '07/2026', '08/2026'])
        self.assertEqual(
            report.flight_trend.aircraft_hours['YV204E'],
            [Decimal('2.0'), ZERO, ZERO],
        )

    def test_daily_trend_fills_empty_days_and_calculates_income_and_profit(self):
        self.create_flight(session_date=date(2026, 6, 10))
        self.create_flight(
            session_date=date(2026, 6, 12),
            session_flight_hours=Decimal('1.0'),
            fuel_consumed=Decimal('10.0'),
        )

        report = get_production_report(
            ProductionFilters(date(2026, 6, 10), date(2026, 6, 12))
        )

        self.assertEqual(report.flight_trend.grouping, 'daily')
        self.assertEqual(report.flight_trend.labels, ['10/06', '11/06', '12/06'])
        self.assertEqual(
            report.flight_trend.flight_hours,
            [Decimal('2.0'), ZERO, Decimal('1.0')],
        )
        self.assertEqual(
            report.flight_trend.income_usd,
            [Decimal('260.00'), ZERO, Decimal('130.00')],
        )
        self.assertEqual(
            report.flight_trend.operating_profit_usd,
            [Decimal('157.80'), Decimal('0.00'), Decimal('78.90')],
        )

    def test_medium_range_uses_weekly_trend(self):
        self.create_flight(session_date=date(2026, 6, 12))

        report = get_production_report(
            ProductionFilters(date(2026, 6, 1), date(2026, 7, 10))
        )

        self.assertEqual(report.flight_trend.grouping, 'weekly')
        self.assertEqual(report.flight_trend.labels[0], '01/06 - 07/06')
        self.assertEqual(report.flight_trend.flight_hours[1], Decimal('2.0'))

    def test_filters_apply_to_people_aircraft_simulator_and_dates(self):
        self.create_flight()
        self.create_flight(student_id=1000002, session_date=date(2026, 6, 11))
        self.create_sim(student_id=1000002)

        report = get_production_report(
            ProductionFilters(
                date(2026, 6, 10),
                date(2026, 6, 10),
                aircraft_registrations=('YV204E',),
                simulator_ids=(self.simulator.pk,),
                instructor_ids=(2000001,),
                student_ids=(1000001,),
            )
        )

        self.assertEqual(report.totals.flight_hours, Decimal('2.0'))
        self.assertEqual(report.totals.simulator_hours, ZERO)

    def test_rejects_reversed_date_range(self):
        with self.assertRaises(ValidationError):
            get_production_report(
                ProductionFilters(date(2026, 8, 13), date(2026, 6, 5))
            )


ZERO = Decimal('0')
