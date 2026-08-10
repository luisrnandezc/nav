from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import InstructorProfile
from fleet.models import Aircraft
from fms.forms import FlightEvaluation100_120Form

from .factories import StudentProfileFactory, UserFactory


class HviEvaluationRateTests(TestCase):
    def setUp(self):
        self.student = UserFactory(role='STUDENT')
        self.student_profile = StudentProfileFactory(
            user=self.student,
            balance=Decimal('1000.00'),
            flight_hours=Decimal('50.0'),
            nav_flight_hours=Decimal('20.0'),
        )
        self.student_profile.flight_rate = Decimal('95.0')
        self.student_profile.save(update_fields=['flight_rate'])

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

    def valid_form_data(self):
        form = FlightEvaluation100_120Form(user=self.instructor)
        data = {
            name: 'NE'
            for name in form.fields
            if name.startswith(('pre_', 'to_', 'b_ifr_', 'a_ifr_', 'land_', 'emer_', 'gen_'))
        }
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
            'course_type': 'HVI-P',
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
            'comments': 'Evaluación HVI completada satisfactoriamente.',
        })
        return data

    def test_hvi_uses_and_persists_custom_student_rate(self):
        form = FlightEvaluation100_120Form(
            data=self.valid_form_data(),
            user=self.instructor,
        )
        self.assertTrue(form.is_valid(), msg=form.errors.as_json())

        evaluation = form.save()
        self.student_profile.refresh_from_db()

        self.assertEqual(evaluation.hourly_rate_applied, Decimal('95.0'))
        self.assertEqual(evaluation.fuel_rate_applied, Decimal('4.00'))
        self.assertEqual(self.student_profile.balance, Decimal('865.00'))

        evaluation.delete()
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.balance, Decimal('1000.00'))

