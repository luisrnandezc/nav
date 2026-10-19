from concurrent.futures import ThreadPoolExecutor
from datetime import date, time, timedelta
from threading import Barrier

from django.contrib.auth.models import AnonymousUser, Permission
from django.core.exceptions import ValidationError
from django.db import IntegrityError, OperationalError, close_old_connections, connection, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase

from scheduler.models import FPTPeriod, FPTSession
from scheduler.db_errors import is_retryable_fpt_conflict
from scheduler.permissions import can_manage_fpt_schedule, can_view_fpt_schedule
from .factories import UserFactory


class FPTModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.period = FPTPeriod.objects.create(
            start_date=date(2026, 10, 12), end_date=date(2026, 10, 25), is_active=True,
        )
        cls.student = UserFactory(role='STUDENT')
        cls.instructor = UserFactory(role='INSTRUCTOR')

    def session(self, **overrides):
        values = dict(
            period=self.period, date=self.period.start_date, start_hour=10,
            student=self.student, instructor=self.instructor, category=FPTSession.Category.HVI,
        )
        values.update(overrides)
        return FPTSession(**values)

    def test_full_week_period_lengths(self):
        for days in (7, 14, 21, 28):
            with self.subTest(days=days):
                self.period.end_date = self.period.start_date + timedelta(days=days - 1)
                self.period.save()

    def test_invalid_period_lengths_and_missing_dates(self):
        for days in (-1, 0, 1, 6, 29):
            with self.subTest(days=days), self.assertRaises(ValidationError):
                self.period.end_date = self.period.start_date + timedelta(days=days - 1)
                self.period.save()
        with self.assertRaises(ValidationError):
            FPTPeriod().save()
        with self.assertRaises(ValidationError):
            FPTPeriod(start_date='invalid', end_date=self.period.end_date).save()

    def test_period_overlap_including_closed_periods_and_shared_boundary(self):
        self.period.is_active = False
        self.period.save()
        with self.assertRaises(ValidationError):
            FPTPeriod.objects.create(start_date=self.period.end_date,
                                     end_date=self.period.end_date + timedelta(days=6))
        FPTPeriod.objects.create(start_date=self.period.end_date + timedelta(days=1),
                                 end_date=self.period.end_date + timedelta(days=7))

    def test_every_hour_every_weekday_and_fixed_duration(self):
        for day in range(7):
            for hour in range(8, 19):
                with self.subTest(day=day, hour=hour):
                    session = self.session(date=self.period.start_date + timedelta(days=day),
                                           start_hour=hour)
                    session.save()
                    self.assertEqual(session.start_time, time(hour))
                    self.assertEqual(session.end_time, time(hour + 2))
                    session.delete()

    def test_invalid_hours_and_missing_required_fields(self):
        for hour in (7, 19, 8.5, None):
            with self.subTest(hour=hour), self.assertRaises(ValidationError):
                self.session(start_hour=hour).save()
        with self.assertRaises(ValidationError):
            FPTSession().save()
        with self.assertRaises(ValidationError):
            self.session(date='invalid').save()

    def test_period_bounds_and_closed_period(self):
        for day in (self.period.start_date - timedelta(days=1), self.period.end_date + timedelta(days=1)):
            with self.subTest(day=day), self.assertRaises(ValidationError):
                self.session(date=day).save()
        self.session(date=self.period.end_date).save()
        self.period.is_active = False
        self.period.save()
        with self.assertRaises(ValidationError):
            self.session().save()

    def test_close_preserves_sessions_and_allows_payment_correction(self):
        session = self.session()
        session.save()
        self.period.is_active = False
        self.period.save()
        session.status = FPTSession.Status.PAID
        session.notes = 'Pago confirmado manualmente'
        session.save()
        session.start_hour = 12
        with self.assertRaises(ValidationError):
            session.save()

    def test_closed_period_cannot_convert_lock_to_reservation(self):
        session = self.session(status='locked', student=None, instructor=None, category='')
        session.save()
        self.period.is_active = False
        self.period.save()
        session.status = 'pending'
        session.student = self.student
        session.instructor = self.instructor
        session.category = 'ENT'
        with self.assertRaises(ValidationError):
            session.save()

    def test_period_cannot_exclude_existing_sessions(self):
        self.session(date=self.period.end_date).save()
        self.period.end_date -= timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.period.save()

    def test_external_and_mixed_participants(self):
        for student_external, instructor_external in ((True, True), (True, False), (False, True)):
            session = self.session(
                student=None if student_external else self.student,
                external_student_name='  Alumno externo  ' if student_external else '',
                instructor=None if instructor_external else self.instructor,
                external_instructor_name=' Instructor externo ' if instructor_external else '',
            )
            session.save()
            if student_external:
                self.assertEqual(session.external_student_name, 'Alumno externo')
            session.delete()

    def test_participant_exclusivity_missing_names_and_wrong_roles(self):
        invalid = [
            {'student': None}, {'instructor': None}, {'external_student_name': 'Otro'},
            {'external_instructor_name': 'Otro'}, {'student': self.instructor},
            {'instructor': self.student}, {'student': None, 'external_student_name': '  '},
        ]
        for overrides in invalid:
            with self.subTest(overrides=overrides), self.assertRaises(ValidationError):
                self.session(**overrides).save()

    def test_categories_and_statuses(self):
        for category in FPTSession.Category.values:
            session = self.session(category=category)
            session.save()
            session.status = 'paid'
            session.save()
            session.delete()
        for overrides in ({'category': ''}, {'category': '737'}, {'status': 'free'}):
            with self.subTest(overrides=overrides), self.assertRaises(ValidationError):
                self.session(**overrides).save()

    def test_locks_need_no_participants_or_training_category(self):
        self.session(status='locked', student=None, instructor=None, category='').save()
        for overrides in ({}, {'student': None, 'instructor': None},
                          {'student': None, 'instructor': None, 'category': '', 'external_student_name': 'X'}):
            with self.subTest(overrides=overrides), self.assertRaises(ValidationError):
                self.session(start_hour=14, status='locked', **overrides).save()

    def test_overlap_for_every_status_in_both_directions_and_adjacent_allowed(self):
        for status in FPTSession.Status.values:
            occupied = self.session(status=status)
            if status == 'locked':
                occupied.student = occupied.instructor = None
                occupied.category = ''
            occupied.save()
            for hour in (9, 10, 11):
                with self.subTest(status=status, hour=hour), self.assertRaises(ValidationError):
                    self.session(start_hour=hour).save()
            for hour in (8, 12):
                adjacent = self.session(start_hour=hour)
                adjacent.save()
                adjacent.delete()
            occupied.delete()

    def test_rescheduling_excludes_self_and_checks_destination(self):
        first = self.session()
        first.save()
        first.save()
        second = self.session(start_hour=14)
        second.save()
        second.start_hour = 11
        with self.assertRaises(ValidationError):
            second.save()
        second.start_hour = 12
        second.save()

    def test_reschedule_to_another_period(self):
        next_period = FPTPeriod.objects.create(
            start_date=self.period.end_date + timedelta(days=1),
            end_date=self.period.end_date + timedelta(days=7), is_active=True,
        )
        session = self.session()
        session.save()
        session.period = next_period
        with self.assertRaises(ValidationError):
            session.save()
        session.date = next_period.start_date
        session.save()

    def test_occupied_period_and_registered_participants_are_protected(self):
        self.session().save()
        for obj in (self.period, self.student, self.instructor):
            with self.assertRaises(ProtectedError):
                obj.delete()

    def test_database_rejects_overlap_when_validation_is_bypassed(self):
        self.session().save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            FPTSession.objects.bulk_create([self.session(start_hour=11)])
        later = self.session(start_hour=14)
        later.save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            FPTSession.objects.filter(pk=later.pk).update(start_hour=11)

    def test_database_rejects_period_overlap_when_validation_is_bypassed(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            FPTPeriod.objects.bulk_create([FPTPeriod(
                start_date=self.period.end_date, end_date=self.period.end_date + timedelta(days=6),
            )])

    def test_database_rejects_invalid_hours_and_assignments(self):
        for overrides in ({'start_hour': 19}, {'student': None}, {'status': 'free'}):
            with self.subTest(overrides=overrides), self.assertRaises(IntegrityError), transaction.atomic():
                FPTSession.objects.bulk_create([self.session(**overrides)])


class FPTPermissionTests(TestCase):
    def test_view_manage_and_role_policy(self):
        view = Permission.objects.get(codename='view_fpt_schedule', content_type__app_label='scheduler')
        manage = Permission.objects.get(codename='manage_fpt_schedule', content_type__app_label='scheduler')
        for role in ('STUDENT', 'STAFF', 'INSTRUCTOR'):
            for permissions in ([], [view], [manage], [view, manage]):
                user = UserFactory(role=role)
                user.user_permissions.set(permissions)
                allowed_role = role != 'STUDENT'
                self.assertEqual(can_view_fpt_schedule(user), allowed_role and bool(permissions))
                self.assertEqual(can_manage_fpt_schedule(user), allowed_role and manage in permissions)
        self.assertFalse(can_view_fpt_schedule(AnonymousUser()))
        self.assertFalse(can_manage_fpt_schedule(AnonymousUser()))
        user = UserFactory(role='STAFF', is_active=False, is_superuser=True)
        self.assertFalse(can_view_fpt_schedule(user))
        self.assertFalse(can_manage_fpt_schedule(user))


class FPTConcurrencyTests(TransactionTestCase):
    """Separate connections race at the database boundary, bypassing clean()."""

    def test_simultaneous_overlapping_inserts(self):
        self.race_occupancy('insert')

    def test_simultaneous_overlapping_reschedules(self):
        self.race_occupancy('update')

    def test_simultaneous_model_saves(self):
        self.race_occupancy('save')

    def race_occupancy(self, operation):
        period = FPTPeriod.objects.create(
            start_date=date(2026, 10, 12), end_date=date(2026, 10, 18), is_active=True,
        )
        existing = []
        if operation == 'update':
            existing = FPTSession.objects.bulk_create([
                FPTSession(period=period, date=period.start_date, start_hour=hour, status='locked')
                for hour in (8, 16)
            ])
        barrier = Barrier(2)

        def insert(hour):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                session = FPTSession(period_id=period.pk, date=period.start_date,
                                     start_hour=hour, status='locked')
                if operation == 'insert':
                    FPTSession.objects.bulk_create([session])
                elif operation == 'save':
                    session.save()
                else:
                    FPTSession.objects.filter(pk=existing[hour - 10].pk).update(start_hour=hour)
                return 'created'
            except (IntegrityError, ValidationError):
                return 'conflict'
            except OperationalError as exc:
                # Exclusion checks may deadlock for raw concurrent writes;
                # PostgreSQL aborts one transaction, preserving non-overlap.
                if not is_retryable_fpt_conflict(exc, connection.vendor):
                    raise
                return 'busy' if connection.vendor == 'sqlite' else 'conflict'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(insert, [10, 11]))
        if connection.vendor == 'sqlite' and outcomes.count('created') == 0:
            # Shared in-memory SQLite can reject both read-to-write upgrades.
            # Both API callers receive retryable 409s; after rollback a fresh
            # attempt must succeed. PostgreSQL must always produce one winner.
            self.assertCountEqual(outcomes, ['busy', 'busy'])
            if operation == 'update':
                FPTSession.objects.filter(pk=existing[0].pk).update(start_hour=10)
            else:
                FPTSession.objects.create(period=period, date=period.start_date,
                                           start_hour=10, status='locked')
        else:
            self.assertCountEqual(['conflict' if item == 'busy' else item for item in outcomes],
                                  ['created', 'conflict'])
        self.assertEqual(FPTSession.objects.count(), 2 if operation == 'update' else 1)
        hours = list(FPTSession.objects.order_by('start_hour').values_list('start_hour', flat=True))
        if len(hours) == 2:
            self.assertGreaterEqual(hours[1] - hours[0], 2)
