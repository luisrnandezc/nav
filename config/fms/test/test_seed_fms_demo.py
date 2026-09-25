"""Exercise demo seeding through real forms and verify its safety boundaries."""
from io import StringIO
from decimal import Decimal
from unittest.mock import patch

from django.core.management import call_command
from django.conf import settings
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User, StudentProfile
from fleet.models import Aircraft
from fms.management.commands.seed_fms_demo import ACCOUNTS, AIRCRAFT, MARKER, PASSWORD, Command
from transactions.models import StudentTransaction
from transactions.student_activity import FLIGHT_MODELS, student_activity


@override_settings(DEBUG=True, ON_PYTHONANYWHERE=False, PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class SeedFmsDemoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_fms_demo', as_of='2026-09-24', stdout=StringIO())

    def run_seed(self, **kwargs):
        output = StringIO()
        call_command('seed_fms_demo', as_of='2026-09-24', stdout=output, **kwargs)
        return output.getvalue()

    def test_seeded_balances_hours_and_aircraft_totals_reconcile(self):
        for username, _, role, _, _ in ACCOUNTS:
            user = User.objects.get(username=username)
            self.assertTrue(user.check_password(PASSWORD))
            if role != 'STUDENT':
                continue
            profile = user.student_profile
            activity = student_activity(profile)
            expected = sum((
                row['amount'] if row['credit'] else -row['amount']
                for row in activity['movements'] if not row['pending']
            ), Decimal('0'))
            self.assertEqual(profile.balance, expected)
            self.assertEqual(profile.nav_flight_hours, activity['stats']['total_flight_hours'])
            self.assertFalse(activity['unresolved_fuel'])
        for aircraft in Aircraft.objects.filter(registration__in=AIRCRAFT):
            self.assertEqual(aircraft.fuel_cost, Decimal('3.11'))
            hours = sum((flight.session_flight_hours for _, model in FLIGHT_MODELS
                         for flight in model.objects.filter(aircraft=aircraft)), Decimal('0'))
            self.assertEqual(aircraft.total_hours, hours)
        self.assertLess(User.objects.get(username='demo_fms_debt').student_profile.balance, 0)
        self.assertGreater(User.objects.get(username='demo_fms_student').student_profile.balance, 0)
        self.assertEqual(User.objects.get(username='demo_fms_empty').student_profile.balance, 0)
        self.assertEqual(StudentTransaction.objects.filter(fuel_liters__isnull=False).count(), 1)

    def test_repeat_is_noop_and_reset_rebuilds_only_demo_data(self):
        unrelated = User.objects.create_user('real_user', 'real@example.invalid', 7654321, 'secret', role='STUDENT')
        StudentProfile.objects.create(user=unrelated, student_age=25, balance=Decimal('123'))
        before = list(StudentTransaction.objects.values_list('pk', 'amount'))
        self.assertIn('already exists', self.run_seed())
        self.assertEqual(before, list(StudentTransaction.objects.values_list('pk', 'amount')))
        self.run_seed(reset=True)
        self.assertEqual(StudentTransaction.objects.count(), len(before))
        self.assertEqual(unrelated.student_profile.balance, Decimal('123'))
        self.assertEqual(sum(model.objects.count() for _, model in FLIGHT_MODELS), 34)
        self.test_seeded_balances_hours_and_aircraft_totals_reconcile()

    def test_reset_refuses_manual_transactions(self):
        profile = User.objects.get(username='demo_fms_student').student_profile
        manual = StudentTransaction.objects.create(student_profile=profile, amount=1, notes='Manual UI test')
        count = StudentTransaction.objects.count()
        with self.assertRaisesMessage(CommandError, 'manual or non-demo transactions'):
            self.run_seed(reset=True)
        self.assertEqual(StudentTransaction.objects.count(), count)
        self.assertTrue(StudentTransaction.objects.filter(pk=manual.pk).exists())

    def test_reset_refuses_non_demo_flight_on_demo_aircraft(self):
        _, model = FLIGHT_MODELS[0]
        flight = model.objects.first()
        model.objects.filter(pk=flight.pk).update(student_id=7654321)
        with self.assertRaisesMessage(CommandError, 'manual or non-demo flight'):
            self.run_seed(reset=True)
        self.assertTrue(model.objects.filter(pk=flight.pk, student_id=7654321).exists())

    def test_students_can_open_overview_logbook_and_full_stats(self):
        for username in ('demo_fms_student', 'demo_fms_advanced', 'demo_fms_empty'):
            self.client.force_login(User.objects.get(username=username))
            for route in ('transactions:student_overview', 'fms:student_flightlog', 'fms:student_stats_page'):
                self.assertEqual(self.client.get(reverse(route)).status_code, 200)
        self.client.force_login(User.objects.get(username='demo_fms_student'))
        page = self.client.get(reverse('transactions:student_overview'))
        self.assertTrue(page.context['page_obj'].has_next())
        self.assertContains(page, 'Combustible registrado posteriormente')
        self.client.force_login(User.objects.get(username='demo_fms_staff'))
        self.assertEqual(self.client.get(reverse('transactions:add_fuel_transaction')).status_code, 200)

    def test_evaluation_routes_restrict_students_to_their_own_flights(self):
        """Students receive 404 from every evaluation route for another student's flight."""
        outsider = User.objects.get(username='demo_fms_empty')
        self.client.force_login(outsider)

        for form_type, model in FLIGHT_MODELS:
            evaluation = model.objects.first()
            self.assertNotEqual(evaluation.student_id, outsider.national_id)
            route_kwargs = {'form_type': form_type, 'evaluation_id': evaluation.pk}
            for route_name in ('session_detail', 'pdf_download_waiting_page', 'download_pdf'):
                response = self.client.get(reverse(f'fms:{route_name}', kwargs=route_kwargs))
                self.assertEqual(response.status_code, 404)

    def test_students_instructors_and_staff_keep_their_expected_flight_access(self):
        """Owners can use all flight routes while instructors and staff retain detail access."""
        student = User.objects.get(username='demo_fms_student')
        _, model = FLIGHT_MODELS[0]
        evaluation = model.objects.filter(student_id=student.national_id).first()
        route_kwargs = {'form_type': '0_100', 'evaluation_id': evaluation.pk}

        self.client.force_login(student)
        self.assertEqual(
            self.client.get(reverse('fms:session_detail', kwargs=route_kwargs)).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse('fms:pdf_download_waiting_page', kwargs=route_kwargs)).status_code,
            200,
        )
        with patch('fms.views.weasyprint.HTML.write_pdf', return_value=b'%PDF-1.4'):
            response = self.client.get(reverse('fms:download_pdf', kwargs=route_kwargs))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

        for username in ('demo_fms_instructor', 'demo_fms_staff'):
            self.client.force_login(User.objects.get(username=username))
            response = self.client.get(reverse('fms:session_detail', kwargs=route_kwargs))
            self.assertEqual(response.status_code, 200)

    def test_reset_failure_rolls_back_existing_dataset(self):
        before = list(StudentTransaction.objects.values_list('pk', 'amount'))
        with patch.object(Command, 'seed_scenarios', side_effect=CommandError('example failure')):
            with self.assertRaisesMessage(CommandError, 'example failure'):
                self.run_seed(reset=True)
        self.assertEqual(before, list(StudentTransaction.objects.values_list('pk', 'amount')))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend')
    def test_seed_discards_notification_emails_and_restores_backend(self):
        with patch('django.core.mail.backends.smtp.EmailBackend.send_messages') as smtp:
            self.run_seed(reset=True)
        smtp.assert_not_called()
        self.assertTrue(StudentTransaction.objects.filter(confirmed=False).exists())
        self.assertEqual(settings.EMAIL_BACKEND, 'django.core.mail.backends.smtp.EmailBackend')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend')
    def test_failed_seed_restores_email_backend(self):
        with patch.object(Command, 'seed_scenarios', side_effect=CommandError('example failure')):
            with self.assertRaises(CommandError):
                self.run_seed(reset=True)
        self.assertEqual(settings.EMAIL_BACKEND, 'django.core.mail.backends.smtp.EmailBackend')


@override_settings(DEBUG=True, ON_PYTHONANYWHERE=False)
class SeedFmsDemoGuardTests(TestCase):
    def test_production_is_refused_even_with_reset(self):
        for settings in ({'DEBUG': False}, {'ON_PYTHONANYWHERE': True}):
            with self.settings(**settings):
                with self.assertRaisesMessage(CommandError, 'disabled in production'):
                    call_command('seed_fms_demo', reset=True, stdout=StringIO())
        self.assertFalse(User.objects.exists())

    def test_reserved_username_collision_is_not_adopted(self):
        user = User.objects.create_user('demo_fms_student', 'existing@example.invalid', 1234567, 'secret', role='STUDENT')
        with self.assertRaisesMessage(CommandError, 'conflicts with an existing account'):
            call_command('seed_fms_demo', stdout=StringIO())
        self.assertEqual(User.objects.get(pk=user.pk).email, 'existing@example.invalid')
        self.assertFalse(Aircraft.objects.filter(registration__in=AIRCRAFT).exists())

    def test_aircraft_collision_rolls_back_without_changes(self):
        plane = Aircraft.objects.create(registration=AIRCRAFT[0], serial_number='real',
                                        manufacturer='Piper', model='PA-28', year_manufactured=2000)
        with self.assertRaisesMessage(CommandError, 'aircraft conflicts'):
            call_command('seed_fms_demo', stdout=StringIO())
        self.assertFalse(User.objects.exists())
        self.assertEqual(Aircraft.objects.get(pk=plane.pk).serial_number, 'real')
