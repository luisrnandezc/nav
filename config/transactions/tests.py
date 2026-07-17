from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts.models import StudentProfile, User
from fleet.models import Aircraft
from fms.models import FlightEvaluation0_100, FlightEvaluation100_120

from .models import StudentTransaction


class MissingFuelEvaluationsTest(TestCase):
    """The fuel page lists unresolved evaluations and preserves filter context."""

    def setUp(self):
        self.staff = User.objects.create_superuser(
            username='fuel_staff',
            email='fuel_staff@test.nav',
            national_id=30_000_001,
            password='x',
            role=User.Role.STAFF,
            first_name='Fuel',
            last_name='Staff',
        )
        self.student = self.create_student('fuel_student_1', 30_000_002, 'Ana')
        self.other_student = self.create_student('fuel_student_2', 30_000_003, 'Luis')
        self.aircraft = Aircraft.objects.create(
            manufacturer='Piper',
            model='PA-28',
            registration='YVTEST',
            serial_number='FUEL-TEST-1',
            year_manufactured=2000,
            fuel_cost=Decimal('3.00'),
        )
        self.older_evaluation = self.create_evaluation(
            FlightEvaluation0_100,
            self.student,
            date.today() - timedelta(days=1),
        )
        self.newer_evaluation = self.create_evaluation(
            FlightEvaluation100_120,
            self.other_student,
            date.today(),
        )
        self.completed_evaluation = self.create_evaluation(
            FlightEvaluation0_100,
            self.student,
            date.today(),
            fuel_consumed=Decimal('10.0'),
        )
        self.client.force_login(self.staff)

    def create_student(self, username, national_id, first_name):
        user = User.objects.create_user(
            username=username,
            email=f'{username}@test.nav',
            national_id=national_id,
            password='x',
            role=User.Role.STUDENT,
            first_name=first_name,
            last_name='Student',
        )
        StudentProfile.objects.create(
            user=user,
            student_age=20,
            balance=Decimal('500.00'),
        )
        return user

    def create_evaluation(self, model, student, session_date, fuel_consumed=Decimal('0')):
        return model.objects.create(
            student_id=student.national_id,
            student_first_name=student.first_name,
            student_last_name=student.last_name,
            student_license_type='PPA',
            student_license_number=student.national_id,
            instructor_id=40_000_001,
            instructor_first_name='Test',
            instructor_last_name='Instructor',
            instructor_license_number=40_000_001,
            session_date=session_date,
            aircraft=self.aircraft,
            fuel_consumed=fuel_consumed,
        )

    def test_page_shows_all_unresolved_evaluations_newest_first(self):
        response = self.client.get(reverse('transactions:add_fuel_transaction'))

        self.assertEqual(response.status_code, 200)
        evaluations = response.context['evaluations']
        self.assertEqual(
            [item['evaluation'] for item in evaluations],
            [self.newer_evaluation, self.older_evaluation],
        )
        self.assertNotIn(
            self.completed_evaluation,
            [item['evaluation'] for item in evaluations],
        )

    def test_student_filter_only_shows_that_students_evaluations(self):
        response = self.client.get(
            reverse('transactions:add_fuel_transaction'),
            {'student_national_id': self.student.national_id},
        )

        evaluations = response.context['evaluations']
        self.assertEqual([item['evaluation'] for item in evaluations], [self.older_evaluation])
        self.assertEqual(response.context['active_student_filter'], self.student.national_id)

    def test_update_from_unfiltered_page_returns_to_unfiltered_results(self):
        response = self.client.post(reverse('transactions:update_fuel_consumed'), {
            'evaluation_id': self.older_evaluation.pk,
            'model_type': 'flightevaluation0_100',
            'fuel_consumed': '10.0',
            'active_student_filter': '',
        })

        self.assertRedirects(response, reverse('transactions:add_fuel_transaction'))
        self.older_evaluation.refresh_from_db()
        self.assertEqual(self.older_evaluation.fuel_consumed, Decimal('10.0'))
        self.assertTrue(StudentTransaction.objects.filter(
            student_profile=self.student.student_profile,
            amount=Decimal('30.00'),
            type=StudentTransaction.DEBIT,
            confirmed=True,
        ).exists())

    def test_update_preserves_active_student_filter(self):
        response = self.client.post(reverse('transactions:update_fuel_consumed'), {
            'evaluation_id': self.older_evaluation.pk,
            'model_type': 'flightevaluation0_100',
            'fuel_consumed': '10.0',
            'active_student_filter': str(self.student.national_id),
        })

        expected_url = (
            f"{reverse('transactions:add_fuel_transaction')}"
            f"?student_national_id={self.student.national_id}"
        )
        self.assertRedirects(response, expected_url)

    @patch('transactions.views.StudentTransaction.objects.create', side_effect=RuntimeError('failure'))
    def test_fuel_update_rolls_back_when_transaction_creation_fails(self, _create_transaction):
        self.client.post(reverse('transactions:update_fuel_consumed'), {
            'evaluation_id': self.older_evaluation.pk,
            'model_type': 'flightevaluation0_100',
            'fuel_consumed': '10.0',
            'active_student_filter': '',
        })

        self.older_evaluation.refresh_from_db()
        self.assertEqual(self.older_evaluation.fuel_consumed, Decimal('0.0'))
