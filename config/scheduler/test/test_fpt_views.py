import json
from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.db import OperationalError, connection
from django.test import Client, TestCase
from django.urls import reverse

from scheduler.models import FPTPeriod, FPTSession, FlightPeriod, FlightSlot
from .factories import UserFactory


class FPTViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.period = FPTPeriod.objects.create(
            start_date=date(2026, 10, 12), end_date=date(2026, 10, 25), is_active=True,
        )
        cls.student = UserFactory(role='STUDENT')
        cls.instructor = UserFactory(role='INSTRUCTOR')
        cls.manager = UserFactory(role='STAFF')
        cls.viewer = UserFactory(role='STAFF')
        cls.unprivileged = UserFactory(role='STAFF')
        view = Permission.objects.get(codename='view_fpt_schedule', content_type__app_label='scheduler')
        manage = Permission.objects.get(codename='manage_fpt_schedule', content_type__app_label='scheduler')
        cls.manager.user_permissions.add(manage)  # Management alone includes viewing.
        cls.viewer.user_permissions.add(view)
        cls.student.user_permissions.add(view, manage)  # Still no student self-booking.
        cls.session = FPTSession.objects.create(
            period=cls.period, date=cls.period.start_date, start_hour=10,
            student=cls.student, instructor=cls.instructor, category='HVI',
        )

    def setUp(self):
        self.client.force_login(self.manager)

    def url(self, name, *args):
        return reverse(f'scheduler:fpt_{name}', args=args)

    def post(self, name, data=None, *args):
        return self.client.post(self.url(name, *args), data=json.dumps(data or {}),
                                content_type='application/json')

    def reservation(self, **changes):
        data = {
            'period': self.period.pk, 'date': '2026-10-12', 'start_hour': 14,
            'status': 'pending', 'student': self.student.pk,
            'instructor': self.instructor.pk, 'category': 'ENT', 'notes': 'Informal',
        }
        data.update(changes)
        return data

    def read_routes(self):
        return [('periods', ()), ('period_detail', (self.period.pk,)),
                ('session_detail', (self.session.pk,))]

    def write_routes(self):
        return [
            ('periods', ()), ('period_detail', (self.period.pk,)),
            ('delete_period', (self.period.pk,)), ('create_session', ()),
            ('session_detail', (self.session.pk,)), ('delete_session', (self.session.pk,)),
        ]

    def test_manager_and_viewer_can_read(self):
        for user in (self.manager, self.viewer):
            self.client.force_login(user)
            for name, args in self.read_routes():
                with self.subTest(user=user.pk, route=name):
                    response = self.client.get(self.url(name, *args))
                    self.assertEqual(response.status_code, 200)
                    self.assertIn('no-store', response.headers['Cache-Control'])
            response = self.client.get(self.url('periods')).json()
            self.assertEqual(response['can_manage'], user == self.manager)
            self.assertEqual([item['value'] for item in response['categories']], FPTSession.Category.values)

    def test_viewer_cannot_write_or_list_participant_directory(self):
        self.client.force_login(self.viewer)
        for name, args in self.write_routes():
            with self.subTest(route=name):
                self.assertEqual(self.post(name, {}, *args).status_code, 403)
        self.assertEqual(self.client.get(self.url('participants')).status_code, 403)
        self.assertEqual(FPTSession.objects.count(), 1)
        self.assertEqual(FPTPeriod.objects.count(), 1)

    def test_permissions_are_enforced_before_object_lookup(self):
        for user in (self.student, self.unprivileged):
            self.client.force_login(user)
            for name, args in self.read_routes():
                self.assertEqual(self.client.get(self.url(name, *args)).status_code, 403)
            for name, args in self.write_routes():
                self.assertEqual(self.post(name, {}, *args).status_code, 403)
            self.assertEqual(self.client.get(self.url('session_detail', 99999)).status_code, 403)

    def test_anonymous_redirects_to_login_for_all_routes(self):
        self.client.logout()
        for name, args in self.read_routes() + [('participants', ())]:
            self.assertEqual(self.client.get(self.url(name, *args)).status_code, 302)
        for name, args in self.write_routes():
            self.assertEqual(self.post(name, {}, *args).status_code, 302)

    def test_instructor_requires_explicit_permissions(self):
        self.client.force_login(self.instructor)
        self.assertEqual(self.client.get(self.url('periods')).status_code, 403)
        self.instructor.user_permissions.add(*self.viewer.user_permissions.all())
        self.assertEqual(self.client.get(self.url('periods')).status_code, 200)
        self.assertEqual(self.post('create_session', self.reservation()).status_code, 403)
        self.instructor.user_permissions.add(*self.manager.user_permissions.all())
        self.assertEqual(self.post('create_session', self.reservation()).status_code, 201)

    def test_period_create_edit_close_reopen_and_delete(self):
        response = self.post('periods', {'start_date': '2026-11-03', 'end_date': '2026-11-10'})
        self.assertEqual(response.status_code, 201, response.content)
        pk = response.json()['period']['id']
        self.assertFalse(response.json()['period']['is_active'])
        for active in (True, False, True):
            response = self.post('period_detail', {'is_active': active}, pk)
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual(response.json()['period']['is_active'], active)
        self.assertEqual(self.post('period_detail', {'end_date': '2026-11-12'}, pk).status_code, 200)
        self.assertEqual(self.post('delete_period', {}, pk).status_code, 200)
        self.assertFalse(FPTPeriod.objects.filter(pk=pk).exists())

    def test_invalid_periods_and_occupied_period_deletion(self):
        for data in (
            {'start_date': '2026-11-01', 'end_date': '2026-11-06'},
            {'start_date': '2026-11-01', 'end_date': '2026-11-29'},
            {'start_date': '2026-10-25', 'end_date': '2026-10-31'},
            {'start_date': 'bad', 'end_date': '2026-11-07'},
        ):
            with self.subTest(data=data):
                self.assertEqual(self.post('periods', data).status_code, 400)
        self.assertEqual(self.post('delete_period', {}, self.period.pk).status_code, 409)
        self.assertEqual(self.post('period_detail', {'start_date': '2026-10-13'}, self.period.pk).status_code, 400)

    def test_free_hours_respect_two_hour_occupancy_and_period_closure(self):
        FPTSession.objects.create(period=self.period, date=self.period.start_date,
                                  start_hour=18, status='locked')
        data = self.client.get(self.url('period_detail', self.period.pk)).json()
        self.assertEqual(len(data['days']), 14)
        self.assertEqual(data['days'][0]['available_start_hours'], [8, 12, 13, 14, 15, 16])
        self.assertEqual(data['days'][6]['available_start_hours'], list(range(8, 19)))  # Sunday
        self.assertEqual(data['days'][-1]['date'], '2026-10-25')
        self.assertEqual(self.post('period_detail', {'is_active': False}, self.period.pk).status_code, 200)
        data = self.client.get(self.url('period_detail', self.period.pk)).json()
        self.assertTrue(all(day['available_start_hours'] == [] for day in data['days']))
        self.assertEqual(len(data['sessions']), 2)
        self.assertEqual(self.post('create_session', self.reservation()).status_code, 400)

    def test_session_create_read_pay_edit_reschedule_delete(self):
        response = self.post('create_session', self.reservation())
        self.assertEqual(response.status_code, 201, response.content)
        data = response.json()['session']
        pk = data['id']
        self.assertEqual((data['start_time'], data['end_time']), ('14:00', '16:00'))
        self.assertEqual(data['student'], self.student.pk)
        self.assertEqual(data['status'], 'pending')
        response = self.post('session_detail', {'status': 'paid', 'notes': 'Pago manual'}, pk)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['session']['status'], 'paid')
        self.assertEqual(response.json()['session']['notes'], 'Pago manual')
        response = self.post('session_detail', {'date': '2026-10-18', 'start_hour': 18}, pk)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['session']['end_time'], '20:00')
        self.assertEqual(self.client.get(self.url('session_detail', pk)).status_code, 200)
        self.assertEqual(self.post('delete_session', {}, pk).status_code, 200)
        self.assertFalse(FPTSession.objects.filter(pk=pk).exists())
        self.assertEqual(FlightPeriod.objects.count(), 0)
        self.assertEqual(FlightSlot.objects.count(), 0)

    def test_informal_sessions_support_external_and_mixed_participants(self):
        response = self.post('create_session', self.reservation(
            student=None, external_student_name='  Alumno externo  ',
            instructor=None, external_instructor_name=' Instructor externo ',
        ))
        self.assertEqual(response.status_code, 201, response.content)
        data = response.json()['session']
        self.assertEqual(data['student_name'], 'Alumno externo')
        self.assertEqual(data['instructor_name'], 'Instructor externo')
        response = self.post('session_detail', {'instructor': self.instructor.pk,
                                                'external_instructor_name': ''}, data['id'])
        self.assertEqual(response.status_code, 200, response.content)

    def test_lock_create_convert_and_remove(self):
        response = self.post('create_session', {
            'period': self.period.pk, 'date': '2026-10-12', 'start_hour': 14,
            'status': 'locked', 'notes': 'Mantenimiento',
        })
        self.assertEqual(response.status_code, 201, response.content)
        pk = response.json()['session']['id']
        self.assertIsNone(response.json()['session']['student'])
        self.assertEqual(self.post('create_session', self.reservation(start_hour=15)).status_code, 400)
        self.assertEqual(self.post('session_detail', self.reservation(), pk).status_code, 200)
        response = self.post('session_detail', {
            'status': 'locked', 'student': None, 'instructor': None, 'category': '',
            'external_student_name': '', 'external_instructor_name': '',
        }, pk)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.post('delete_session', {}, pk).status_code, 200)

    def test_invalid_session_payloads_do_not_create_occupancy(self):
        for changes in (
            {'start_hour': 7}, {'start_hour': 19}, {'start_hour': 8.5},
            {'date': '2026-10-26'}, {'date': 'bad'}, {'period': 99999},
            {'student': self.instructor.pk}, {'instructor': self.student.pk},
            {'student': None, 'external_student_name': '   '},
            {'external_instructor_name': 'Duplicate'}, {'category': '737'},
            {'category': ''}, {'status': 'free'}, {'status': 'locked'},
            {'aircraft': 1}, {'end_time': '17:00'},
        ):
            with self.subTest(changes=changes):
                response = self.post('create_session', self.reservation(**changes))
                self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(FPTSession.objects.count(), 1)

    def test_failed_reschedule_keeps_original_occupancy(self):
        response = self.post('session_detail', {'start_hour': 11}, self.session.pk)
        # The session excludes itself, so this move succeeds.
        self.assertEqual(response.status_code, 200, response.content)
        FPTSession.objects.create(period=self.period, date=self.period.start_date,
                                  start_hour=14, status='locked')
        self.assertEqual(self.post('session_detail', {'start_hour': 13}, self.session.pk).status_code, 400)
        self.session.refresh_from_db()
        self.assertEqual(self.session.start_hour, 11)

    def test_closed_period_allows_payment_correction_but_not_rescheduling(self):
        self.period.is_active = False
        self.period.save()
        self.assertEqual(self.post('session_detail', {'status': 'paid'}, self.session.pk).status_code, 200)
        self.assertEqual(self.post('session_detail', {'start_hour': 14}, self.session.pk).status_code, 400)

    def test_participant_choices_include_all_registered_roles_without_availability_checks(self):
        response = self.client.get(self.url('participants'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn({'id': self.student.pk, 'name': self.student.get_full_name()}, data['students'])
        self.assertIn({'id': self.instructor.pk, 'name': self.instructor.get_full_name()}, data['instructors'])
        for choice in data['students'] + data['instructors']:
            self.assertEqual(set(choice), {'id', 'name'})
            self.assertNotIn(choice['id'], [self.manager.pk, self.viewer.pk])

    def test_form_encoded_payload_supported(self):
        response = self.client.post(self.url('create_session'), self.reservation())
        self.assertEqual(response.status_code, 201, response.content)

    def test_malformed_json_and_unknown_fields_return_validation_errors(self):
        for body in ('{bad', '[]', 'null', '"text"', '{"notes": {"bad": true}}'):
            response = self.client.post(self.url('create_session'), body, content_type='application/json')
            self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(self.post('period_detail', {'id': 123}, self.period.pk).status_code, 400)
        self.assertEqual(self.post('create_session', {}).status_code, 400)

    def test_unsupported_methods_do_not_write(self):
        for name, args in [('delete_session', (self.session.pk,)), ('delete_period', (self.period.pk,)),
                           ('create_session', ())]:
            self.assertEqual(self.client.get(self.url(name, *args)).status_code, 405)
        for name, args in self.read_routes() + [('participants', ())]:
            self.assertEqual(self.client.delete(self.url(name, *args)).status_code, 405)
        self.assertEqual(self.post('participants').status_code, 405)
        self.assertEqual(FPTSession.objects.count(), 1)

    def test_missing_objects_return_404(self):
        for name in ('period_detail', 'session_detail'):
            self.assertEqual(self.client.get(self.url(name, 99999)).status_code, 404)
            self.assertEqual(self.post(name, {}, 99999).status_code, 404)
        for name in ('delete_period', 'delete_session'):
            self.assertEqual(self.post(name, {}, 99999).status_code, 404)

    def test_csrf_is_required_for_every_write_route(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.manager)
        for name, args in self.write_routes():
            self.assertEqual(client.post(self.url(name, *args), {}).status_code, 403)
        token = 'a' * 32
        client.cookies['csrftoken'] = token
        response = client.post(self.url('create_session'), json.dumps(self.reservation()),
                               content_type='application/json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 201, response.content)

    def test_database_overlap_conflict_is_safe_and_transaction_is_rolled_back(self):
        # Emulate another request winning after validation: skip the optimistic
        # model check and let the real database guard reject the write.
        with patch.object(FPTSession, 'full_clean'):
            response = self.post('create_session', self.reservation(start_hour=11))
        self.assertEqual(response.status_code, 409, response.content)
        self.assertNotIn('scheduler_fpt', response.content.decode())
        self.assertEqual(FPTSession.objects.count(), 1)
        self.assertEqual(self.post('create_session', self.reservation()).status_code, 201)

    def test_database_period_conflict_is_safe(self):
        with patch.object(FPTPeriod, 'full_clean'):
            response = self.post('periods', {'start_date': '2026-10-20', 'end_date': '2026-10-27'})
        self.assertEqual(response.status_code, 409, response.content)
        self.assertEqual(FPTPeriod.objects.count(), 1)

    def test_sqlite_busy_writer_returns_conflict_and_other_errors_are_not_masked(self):
        if connection.vendor == 'sqlite':
            with patch.object(FPTSession, 'save', side_effect=OperationalError('database is locked')):
                self.assertEqual(self.post('create_session', self.reservation()).status_code, 409)
        with patch.object(FPTSession, 'save', side_effect=OperationalError('connection failed')):
            with self.assertRaises(OperationalError):
                self.post('create_session', self.reservation())
