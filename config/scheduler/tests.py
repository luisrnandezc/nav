from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import StudentProfile, User

from .models import CancellationsFee

# Import all test classes to make them discoverable
from .test.test_model_flight_period import FlightPeriodModelTest
from .test.test_model_flight_slot import FlightSlotModelTest
from .test.test_model_flight_request import FlightRequestModelTest
from .test.test_views import FlightRequestViewTest, FlightPeriodViewTest, ChangeSlotStatusViewTest
from .test.test_forms import CreateFlightPeriodFormTest


class CancellationsFeeReimbursementTest(TestCase):
    """Cancellation fees reimburse their persisted student exactly once."""

    def setUp(self):
        self.student = User.objects.create_user(
            username='fee_student',
            email='fee_student@test.nav',
            national_id=20_000_001,
            password='x',
            role=User.Role.STUDENT,
            first_name='Fee',
            last_name='Student',
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student,
            student_age=20,
            balance=Decimal('400.00'),
        )
        self.fee = CancellationsFee.objects.create(
            student_profile=self.student_profile,
            cancelled_by_name=self.student.get_full_name(),
            amount=Decimal('75.00'),
        )

    def test_reimburse_updates_balance_without_flight_request(self):
        self.fee.reimburse()

        self.student_profile.refresh_from_db()
        self.fee.refresh_from_db()

        self.assertEqual(self.student_profile.balance, Decimal('475.00'))
        self.assertIsNotNone(self.fee.reimbursed_at)
        self.assertTrue(CancellationsFee.objects.filter(pk=self.fee.pk).exists())

    def test_reimburse_cannot_be_applied_twice(self):
        self.fee.reimburse()

        with self.assertRaisesMessage(ValidationError, 'Esta multa ya fue reembolsada'):
            self.fee.reimburse()

        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.balance, Decimal('475.00'))

    def test_reimburse_without_student_keeps_fee_and_reports_error(self):
        self.fee.student_profile = None
        self.fee.save(update_fields=('student_profile',))

        with self.assertRaisesMessage(ValidationError, 'No se pudo identificar al estudiante'):
            self.fee.reimburse()

        self.assertTrue(CancellationsFee.objects.filter(pk=self.fee.pk).exists())
