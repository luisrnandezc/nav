from decimal import Decimal
from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase
from django.utils import timezone

from accounts.models import InstructorProfile
from fleet.models import Aircraft
from fms.forms import (
    FlightEvaluation0_100Form,
    FlightEvaluation100_120Form,
    FlightEvaluation120_170Form,
)

from .factories import StudentProfileFactory, UserFactory


class FlightEvaluationAccountingTests(TestCase):
    FORM_CASES = (
        ('PPA', FlightEvaluation0_100Form, 'PPA-P'),
        ('HVI', FlightEvaluation100_120Form, 'HVI-P'),
        ('PCA', FlightEvaluation120_170Form, 'PCA-P'),
    )

    def setUp(self):
        self.student = UserFactory(role='STUDENT')
        self.student_profile = StudentProfileFactory(
            user=self.student,
            balance=Decimal('1000.00'),
            flight_hours=Decimal('50.0'),
            nav_flight_hours=Decimal('20.0'),
        )
        self.instructor = UserFactory(role='INSTRUCTOR')
        InstructorProfile.objects.create(
            user=self.instructor,
            instructor_type='VUELO',
            instructor_license_type='PCA',
        )
        self.aircraft = Aircraft.objects.create(
            manufacturer='Piper',
            model='PA-28',
            registration='YV-RATE',
            serial_number='RATE-001',
            year_manufactured=1980,
            hourly_rate=Decimal('130.0'),
            fuel_cost=Decimal('4.00'),
            total_hours=Decimal('1000.0'),
        )

    def valid_form_data(self, form_class, course_type, **overrides):
        form = form_class(user=self.instructor)
        data = {}
        for name, field in form.fields.items():
            if hasattr(field, 'choices') and name != 'aircraft':
                data[name] = next(
                    (str(value) for value, _label in field.choices if value != ''),
                    '',
                )

        data.update({
            'instructor_id': self.instructor.national_id,
            'instructor_first_name': self.instructor.first_name,
            'instructor_last_name': self.instructor.last_name,
            'instructor_license_type': 'PCA',
            'instructor_license_number': self.instructor.national_id,
            'student_id': self.student.national_id,
            'student_first_name': self.student.first_name,
            'student_last_name': self.student.last_name,
            'student_license_type': 'PPA',
            'course_type': course_type,
            'flight_rules': 'IFR',
            'solo_flight': 'NO',
            'session_number': '1',
            'session_letter': '',
            'session_date': timezone.localdate().isoformat(),
            'accumulated_flight_hours': '50.0',
            'initial_hourmeter': '100.0',
            'final_hourmeter': '101.0',
            'fuel_consumed': '10.0',
            'aircraft': self.aircraft.pk,
            'session_grade': 'S',
            'comments': 'Evaluación de vuelo completada satisfactoriamente.',
            'discrepancy_type': '',
            'discrepancy_description': '',
        })
        data.update(overrides)
        return data

    def save_evaluation(self, form_class, course_type, **overrides):
        form = form_class(
            data=self.valid_form_data(form_class, course_type, **overrides),
            user=self.instructor,
        )
        self.assertTrue(form.is_valid(), msg=form.errors.as_json())
        return form.save()

    def assert_current_totals(self, balance, flight_hours, nav_hours, aircraft_hours):
        self.student_profile.refresh_from_db()
        self.aircraft.refresh_from_db()
        self.assertEqual(self.student_profile.balance, Decimal(balance))
        self.assertEqual(self.student_profile.flight_hours, Decimal(flight_hours))
        self.assertEqual(self.student_profile.nav_flight_hours, Decimal(nav_hours))
        self.assertEqual(self.aircraft.total_hours, Decimal(aircraft_hours))

    def test_all_evaluation_types_use_aircraft_rates_and_update_totals(self):
        self.student_profile.flight_rate = self.aircraft.hourly_rate
        self.student_profile.save(update_fields=['flight_rate'])

        for label, form_class, course_type in self.FORM_CASES:
            with self.subTest(evaluation=label):
                evaluation = self.save_evaluation(form_class, course_type)

                self.assertEqual(evaluation.hourly_rate_applied, Decimal('130.00'))
                self.assertEqual(evaluation.fuel_rate_applied, Decimal('4.00'))
                self.assertEqual(evaluation.session_flight_hours, Decimal('1.0'))
                self.assert_current_totals('830.00', '51.0', '21.0', '1001.0')

                evaluation.delete()
                self.assert_current_totals('1000.00', '50.0', '20.0', '1000.0')

    def test_all_evaluation_types_use_custom_student_rate(self):
        self.student_profile.flight_rate = Decimal('95.0')
        self.student_profile.save(update_fields=['flight_rate'])

        for label, form_class, course_type in self.FORM_CASES:
            with self.subTest(evaluation=label):
                evaluation = self.save_evaluation(form_class, course_type)

                self.assertEqual(evaluation.hourly_rate_applied, Decimal('95.00'))
                self.assertEqual(evaluation.fuel_rate_applied, Decimal('4.00'))
                self.assert_current_totals('865.00', '51.0', '21.0', '1001.0')

                evaluation.delete()
                self.assert_current_totals('1000.00', '50.0', '20.0', '1000.0')

    def test_yv206e_correction_factor_affects_hours_charge_and_totals(self):
        self.aircraft = Aircraft.objects.get(registration='YV206E')
        self.aircraft.hourly_rate = Decimal('130.0')
        self.aircraft.fuel_cost = Decimal('4.00')
        self.aircraft.hour_correction_factor = Decimal('1.3')
        self.aircraft.total_hours = Decimal('1000.0')
        self.aircraft.save(update_fields=[
            'hourly_rate', 'fuel_cost', 'hour_correction_factor', 'total_hours',
        ])
        self.student_profile.flight_rate = self.aircraft.hourly_rate
        self.student_profile.save(update_fields=['flight_rate'])

        evaluation = self.save_evaluation(FlightEvaluation0_100Form, 'PPA-P')

        self.assertEqual(evaluation.session_flight_hours, Decimal('1.3'))
        self.assert_current_totals('791.00', '51.3', '21.3', '1001.3')

        evaluation.delete()
        self.assert_current_totals('1000.00', '50.0', '20.0', '1000.0')

    def test_deletion_refunds_stored_rates_after_current_rates_change(self):
        self.student_profile.flight_rate = Decimal('95.0')
        self.student_profile.save(update_fields=['flight_rate'])
        evaluation = self.save_evaluation(FlightEvaluation100_120Form, 'HVI-P')

        self.student_profile.flight_rate = Decimal('180.0')
        self.student_profile.save(update_fields=['flight_rate'])
        self.aircraft.hourly_rate = Decimal('200.0')
        self.aircraft.fuel_cost = Decimal('9.00')
        self.aircraft.save(update_fields=['hourly_rate', 'fuel_cost'])

        evaluation.delete()

        self.assert_current_totals('1000.00', '50.0', '20.0', '1000.0')

    def test_creation_rolls_back_if_aircraft_totals_cannot_be_saved(self):
        initial_balance = self.student_profile.balance
        model = FlightEvaluation100_120Form._meta.model
        form = FlightEvaluation100_120Form(
            data=self.valid_form_data(FlightEvaluation100_120Form, 'HVI-P'),
            user=self.instructor,
        )
        self.assertTrue(form.is_valid(), msg=form.errors.as_json())

        with patch.object(Aircraft, 'save', side_effect=DatabaseError('fleet update failed')):
            with self.assertRaises(DatabaseError):
                form.save()

        self.student_profile.refresh_from_db()
        self.aircraft.refresh_from_db()
        self.assertEqual(model.objects.count(), 0)
        self.assertEqual(self.student_profile.balance, initial_balance)
        self.assertEqual(self.student_profile.flight_hours, Decimal('50.0'))
        self.assertEqual(self.student_profile.nav_flight_hours, Decimal('20.0'))
        self.assertEqual(self.aircraft.total_hours, Decimal('1000.0'))
