from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib import admin
from django.test import TestCase
from django.urls import reverse

from accounts.models import InstructorProfile, StudentProfile, User
from fleet.models import Aircraft
from fms.models import FlightEvaluation0_100, FlightEvaluation100_120

from .models import StudentTransaction


class MissingFuelEvaluationsTest(TestCase):
    """The fuel page lists unresolved evaluations and preserves filter context."""

    def test_full_statistics_returns_to_its_entry_point(self):
        self.client.force_login(self.student)
        url = reverse('fms:student_stats_page')
        for origin, target in (
            ('logbook', 'fms:student_flightlog'),
            ('overview', 'transactions:student_overview'),
            ('https://example.invalid', 'transactions:student_overview'),
        ):
            response = self.client.get(url, {'origin': origin})
            self.assertEqual(response.context['back_url'], reverse(target))
        self.client.force_login(self.staff)
        response = self.client.get(reverse('fms:student_stats_detail', args=[self.student.national_id]))
        self.assertEqual(response.context['back_url'], reverse('fms:user_stats_page'))

    def test_demo_marker_is_hidden_without_changing_saved_notes(self):
        from .student_activity import build_transaction_movement

        notes = '[seed_fms_demo:v1] Abono parcial [recibo 123]'
        movement = StudentTransaction.objects.create(
            student_profile=self.student.student_profile, amount=100, notes=notes,
        )
        self.assertEqual(build_transaction_movement(movement)['description'], 'Abono parcial [recibo 123]')
        movement.refresh_from_db()
        self.assertEqual(movement.notes, notes)

    def test_transaction_admin_keeps_accounting_movements_immutable(self):
        model_admin = admin.site._registry[StudentTransaction]
        self.assertFalse(model_admin.has_add_permission(None))
        self.assertFalse(model_admin.has_change_permission(None))
        self.assertFalse(model_admin.has_delete_permission(None))

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
        self.instructor = User.objects.create_user(
            username='fuel_instructor',
            email='fuel_instructor@test.nav',
            national_id=40_000_001,
            password='x',
            role=User.Role.INSTRUCTOR,
            first_name='Test',
            last_name='Instructor',
        )
        InstructorProfile.objects.create(
            user=self.instructor,
            instructor_type=InstructorProfile.FLYING,
            instructor_license_type=InstructorProfile.LICENSE_PCA,
        )
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
            instructor_id=self.instructor.national_id,
            instructor_first_name=self.instructor.first_name,
            instructor_last_name=self.instructor.last_name,
            instructor_license_number=self.instructor.national_id,
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

    def test_late_fuel_snapshot_and_overview_do_not_double_count(self):
        from .student_activity import student_activity

        self.client.post(reverse('transactions:update_fuel_consumed'), {
            'evaluation_id': self.older_evaluation.pk,
            'model_type': 'flightevaluation0_100',
            'fuel_consumed': '10.0',
            'observations': 'Recibo verificado.',
        })
        debit = StudentTransaction.objects.get(student_profile=self.student.student_profile)
        self.assertEqual(debit.fuel_flight_0_100, self.older_evaluation)
        self.assertEqual(debit.fuel_liters, Decimal('10.0'))
        self.assertEqual(debit.fuel_unit_price, Decimal('3.00'))
        self.assertIn(self.older_evaluation.session_date.strftime('%d/%m/%Y'), debit.notes)
        self.assertIn('Recibo verificado.', debit.notes)
        self.aircraft.fuel_cost = Decimal('9.00')
        self.aircraft.save()
        activity = student_activity(self.student.student_profile)
        original = next(row for row in activity['movements'] if row['id'] == f'flight-0_100-{self.older_evaluation.pk}')
        self.assertEqual(original['amount'], Decimal('0.00'))
        self.assertEqual(len(original['fuel_transactions']), 1)
        fuel = next(row for row in activity['movements'] if row['id'] == f'transaction-{debit.pk}')
        self.assertEqual(fuel['amount'], Decimal('30.00'))
        self.assertEqual(fuel['fuel_flight_date'], self.older_evaluation.session_date)
        self.assertEqual(fuel['fuel_aircraft'], 'YVTEST')
        self.assertEqual(fuel['description'], (
            'Combustible registrado posterior a la fecha del vuelo. '
            f'Vuelo del {self.older_evaluation.session_date:%d/%m/%Y} · YVTEST · '
            '10 L × $3/L = $30.00.'
        ))
        self.assertEqual(fuel['url'], reverse('fms:session_detail', args=('0_100', self.older_evaluation.pk)))
        self.student.student_profile.refresh_from_db()
        self.assertEqual(self.student.student_profile.balance, Decimal('470.00'))
        # Re-submitting a completed flight must not debit twice.
        self.client.post(reverse('transactions:update_fuel_consumed'), {
            'evaluation_id': self.older_evaluation.pk, 'model_type': 'flightevaluation0_100',
            'fuel_consumed': '10.0',
        })
        self.assertEqual(StudentTransaction.objects.count(), 1)

    def test_student_overview_is_private_and_pending_credit_is_clear(self):
        own = StudentTransaction.objects.create(
            student_profile=self.student.student_profile, amount=Decimal('75'),
            notes='Mi abono pendiente', confirmed=False,
        )
        StudentTransaction.objects.create(
            student_profile=self.other_student.student_profile, amount=Decimal('999'),
            notes='Privado de otro estudiante', confirmed=False,
        )
        url = reverse('transactions:student_overview')
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.student)
        response = self.client.get(url, {'student_id': self.other_student.national_id})
        self.assertContains(response, 'Mi abono pendiente')
        self.assertContains(response, 'No afecta el saldo')
        self.assertNotContains(response, 'Privado de otro estudiante')
        self.assertContains(response, 'USD 500')
        response = self.client.get(url, {'type': 'credits'})
        self.assertEqual([row['id'] for row in response.context['page_obj']], [f'transaction-{own.pk}'])
        response = self.client.get(url, {'start': 'invalid', 'end': '2026-99-99', 'page': 'invalid'})
        self.assertEqual(response.status_code, 200)

    def test_nonfinite_and_overprecise_fuel_are_rejected(self):
        for value in ('NaN', 'Infinity', '0.01', '1.23'):
            self.client.post(reverse('transactions:update_fuel_consumed'), {
                'evaluation_id': self.older_evaluation.pk, 'model_type': 'flightevaluation0_100',
                'fuel_consumed': value,
            })
        self.assertFalse(StudentTransaction.objects.exists())
        self.older_evaluation.refresh_from_db()
        self.assertEqual(self.older_evaluation.fuel_consumed, 0)

    def test_legacy_fuel_backfill_links_only_unique_matches(self):
        from importlib import import_module
        from django.apps import apps
        from django.db import connection

        self.older_evaluation.fuel_consumed = Decimal('12')
        self.older_evaluation.save()
        debit = StudentTransaction.objects.create(
            student_profile=self.student.student_profile, amount=Decimal('36'),
            type=StudentTransaction.DEBIT, category=StudentTransaction.FLIGHT,
            notes='Combustible: 12.0L - YVTEST - Test Instructor',
        )
        ambiguous = StudentTransaction.objects.create(
            student_profile=self.other_student.student_profile, amount=Decimal('30'),
            type=StudentTransaction.DEBIT, category=StudentTransaction.FLIGHT,
            notes='Combustible: 10.0L - YVTEST - Test Instructor',
        )
        for model in (FlightEvaluation0_100, FlightEvaluation100_120):
            self.create_evaluation(model, self.other_student, date.today(), Decimal('10'))
        migration = import_module('transactions.migrations.0013_link_identifiable_historical_fuel')
        from types import SimpleNamespace
        migration.link_legacy_fuel(apps, SimpleNamespace(connection=connection))
        debit.refresh_from_db()
        ambiguous.refresh_from_db()
        self.assertEqual(debit.fuel_flight_0_100_id, self.older_evaluation.pk)
        self.assertEqual(debit.fuel_unit_price, Decimal('3'))
        self.assertIsNone(ambiguous.fuel_liters)

    def test_summary_uses_saved_rates_and_full_stats_works_without_named_fleet(self):
        from .student_activity import student_activity

        # Bulk update is deliberate: this test reads historical records without posting new charges.
        FlightEvaluation0_100.objects.filter(pk=self.older_evaluation.pk).update(
            session_flight_hours=Decimal('2'), hourly_rate_applied=Decimal('130'),
        )
        self.aircraft.hourly_rate = Decimal('200')
        self.aircraft.save()
        activity = student_activity(self.student.student_profile)
        self.assertEqual(activity['stats']['total_flight_hours_dollars'], Decimal('260'))
        self.assertEqual(activity['liters_per_hour'], Decimal('5'))
        self.assertEqual(activity['dollars_per_hour'], Decimal('145'))
        self.client.force_login(self.student)
        response = self.client.get(reverse('fms:student_stats_page'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_cost'], Decimal('290'))

    def test_pagination_preserves_filters_and_reaches_older_movements(self):
        StudentTransaction.objects.bulk_create([
            StudentTransaction(student_profile=self.student.student_profile, amount=1,
                               notes=f'Abono {index}', confirmed=False)
            for index in range(30)
        ])
        self.client.force_login(self.student)
        response = self.client.get(reverse('transactions:student_overview'), {'type': 'credits', 'page': 2})
        self.assertEqual(len(response.context['page_obj']), 5)
        self.assertContains(response, 'type=credits')
