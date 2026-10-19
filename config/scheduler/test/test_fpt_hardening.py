from concurrent.futures import ThreadPoolExecutor
from datetime import date
from importlib import import_module
from threading import Event

from django.core.exceptions import ValidationError
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature

from scheduler.models import FPTPeriod, FPTSession


class FPTWeekBoundaryTests(TestCase):
    def test_model_and_database_reject_non_week_boundaries(self):
        for start, end in [(date(2026, 11, 3), date(2026, 11, 15)),
                           (date(2026, 11, 2), date(2026, 11, 14))]:
            with self.subTest(start=start, end=end):
                with self.assertRaises(ValidationError):
                    FPTPeriod(start_date=start, end_date=end).save()
                with self.assertRaises(IntegrityError), transaction.atomic():
                    FPTPeriod.objects.bulk_create([FPTPeriod(start_date=start, end_date=end)])


class FPTMigrationTests(TransactionTestCase):
    old = [('scheduler', '0024_fpt_overlap_guards')]
    new = [('scheduler', '0025_fpt_release_hardening')]

    def migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def test_rollback_and_reapply_preserves_overlap_guards_and_data(self):
        period = FPTPeriod.objects.create(start_date=date(2026, 10, 12), end_date=date(2026, 10, 18))
        FPTSession.objects.bulk_create([
            FPTSession(period=period, date=period.start_date, start_hour=10, status='locked'),
        ])
        try:
            old_apps = self.migrate(self.old)
            old_session = old_apps.get_model('scheduler', 'FPTSession')
            with self.assertRaises(IntegrityError), transaction.atomic():
                old_session.objects.create(period_id=period.pk, date=period.start_date,
                                           start_hour=11, status='locked')
        finally:
            self.migrate(self.new)
        self.assertEqual(FPTSession.objects.count(), 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            FPTSession.objects.bulk_create([
                FPTSession(period=period, date=period.start_date, start_hour=11, status='locked'),
            ])
        with self.assertRaises(IntegrityError), transaction.atomic():
            FPTPeriod.objects.bulk_create([
                FPTPeriod(start_date=period.start_date, end_date=period.end_date),
            ])

    def test_migration_reports_existing_invalid_periods_without_rewriting_dates(self):
        old_period = self.migrate(self.old).get_model('scheduler', 'FPTPeriod')
        period = old_period.objects.create(start_date=date(2026, 11, 3), end_date=date(2026, 11, 9))
        try:
            with self.assertRaisesRegex(RuntimeError, f'period IDs before migrating:.*{period.pk}'):
                self.migrate(self.new)
            period.refresh_from_db()
            self.assertEqual(period.start_date, date(2026, 11, 3))
        finally:
            old_period.objects.filter(pk=period.pk).delete()
            self.migrate(self.new)


@skipUnlessDBFeature('has_select_for_update')
class FPTPeriodRaceTests(TransactionTestCase):
    def test_booking_revalidates_after_period_closure(self):
        self.period_change_wins('close')

    def test_booking_revalidates_after_period_shrink(self):
        self.period_change_wins('shrink')

    def test_booking_revalidates_after_period_deletion(self):
        self.period_change_wins('delete')

    def period_change_wins(self, action):
        period = FPTPeriod.objects.create(start_date=date(2026, 10, 12), end_date=date(2026, 10, 25), is_active=True)
        ready = Event()

        def book():
            close_old_connections()
            try:
                ready.set()
                FPTSession.objects.create(period_id=period.pk, date=date(2026, 10, 25),
                                           start_hour=10, status='locked')
                return 'created'
            except ValidationError:
                return 'rejected'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                locked = FPTPeriod.objects.select_for_update().get(pk=period.pk)
                pending = pool.submit(book)
                self.assertTrue(ready.wait(5))
                if action == 'delete':
                    locked.delete()
                else:
                    if action == 'close':
                        locked.is_active = False
                    else:
                        locked.end_date = date(2026, 10, 18)
                    locked.save()
            self.assertEqual(pending.result(timeout=10), 'rejected')
        self.assertFalse(FPTSession.objects.exists())

    def test_shrink_revalidates_after_booking_commits(self):
        period = FPTPeriod.objects.create(start_date=date(2026, 10, 12), end_date=date(2026, 10, 25), is_active=True)
        ready = Event()

        def shrink():
            close_old_connections()
            try:
                ready.set()
                period.end_date = date(2026, 10, 18)
                period.save()
                return 'shrunk'
            except ValidationError:
                return 'rejected'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                FPTSession.objects.create(period=period, date=date(2026, 10, 25), start_hour=10, status='locked')
                pending = pool.submit(shrink)
                self.assertTrue(ready.wait(5))
            self.assertEqual(pending.result(timeout=10), 'rejected')
        period.refresh_from_db()
        self.assertEqual(period.end_date, date(2026, 10, 25))
