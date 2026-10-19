from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier

from django.db import OperationalError, close_old_connections, connection, transaction
from django.test import SimpleTestCase, TransactionTestCase, skipUnlessDBFeature

from scheduler.db_errors import is_retryable_fpt_conflict
from scheduler.models import FPTPeriod, FPTSession


class FPTDatabaseErrorTests(SimpleTestCase):
    def test_only_deadlock_sqlstate_is_classified_as_postgres_conflict(self):
        for attribute in ('pgcode', 'sqlstate'):
            for code in ('40P01', '08006', '53300', None):
                with self.subTest(attribute=attribute, code=code):
                    cause = Exception('driver error')
                    setattr(cause, attribute, code)
                    error = OperationalError('localized message')
                    error.__cause__ = cause
                    self.assertEqual(is_retryable_fpt_conflict(error, 'postgresql'), code == '40P01')
        self.assertFalse(is_retryable_fpt_conflict(OperationalError('deadlock detected'), 'postgresql'))
        self.assertFalse(is_retryable_fpt_conflict(OperationalError('connection failed'), 'sqlite'))
        self.assertTrue(is_retryable_fpt_conflict(OperationalError('database is locked'), 'sqlite'))


@skipUnlessDBFeature('has_select_for_update')
class FPTRealDeadlockTests(TransactionTestCase):
    def test_real_postgres_deadlock_aborts_one_writer_without_partial_commit(self):
        if connection.vendor != 'postgresql':
            self.skipTest('PostgreSQL deadlock SQLSTATE test')
        period = FPTPeriod.objects.create(start_date=date(2026, 10, 12), end_date=date(2026, 10, 18), is_active=True)
        sessions = FPTSession.objects.bulk_create([
            FPTSession(period=period, date=period.start_date, start_hour=hour, status='locked')
            for hour in (8, 14)
        ])
        barrier = Barrier(2)

        def update(index):
            close_old_connections()
            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        # Bound the deliberately induced deadlock if the server
                        # cannot detect it; a timeout remains an unexpected error.
                        cursor.execute("SET LOCAL lock_timeout = '10s'")
                    first, second = sessions[index].pk, sessions[1 - index].pk
                    FPTSession.objects.select_for_update().get(pk=first)
                    FPTSession.objects.filter(pk=first).update(notes=str(index))
                    barrier.wait(timeout=5)
                    FPTSession.objects.select_for_update().get(pk=second)
                    FPTSession.objects.filter(pk=second).update(notes=str(index))
                return 'committed'
            except OperationalError as exc:
                if not is_retryable_fpt_conflict(exc, connection.vendor):
                    raise
                return 'conflict'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(update, [0, 1]))
        self.assertCountEqual(outcomes, ['committed', 'conflict'])
        notes = set(FPTSession.objects.values_list('notes', flat=True))
        self.assertIn(notes, ({'0'}, {'1'}))
