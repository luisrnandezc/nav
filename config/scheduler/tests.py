from decimal import Decimal

from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from accounts.models import StudentProfile, User

from .models import CancellationsFee

# Import all test classes to make them discoverable
from .test.test_model_flight_period import FlightPeriodModelTest
from .test.test_model_flight_slot import FlightSlotModelTest
from .test.test_model_flight_request import FlightRequestModelTest
from .test.test_views import FlightRequestViewTest, FlightPeriodViewTest, ChangeSlotStatusViewTest
from .test.test_forms import CreateFlightPeriodFormTest
from .test.factories import FlightSlotFactory, UserFactory
from . import domain_signals
from .models import FlightSlot


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='scheduler-from@test.com',
)
class InstructorAssignmentEmailTest(TestCase):
    def setUp(self):
        self.instructor = UserFactory(role='INSTRUCTOR')
        self.slot = FlightSlotFactory(instructor=self.instructor)

    def assert_student_line(self, expected):
        with self.captureOnCommitCallbacks(execute=True):
            domain_signals.instructor_assigned_to_slot.send(
                sender=FlightSlot, slot=self.slot, instructor=self.instructor,
            )
            self.assertEqual(len(mail.outbox), 0)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, [self.instructor.email])
        self.assertEqual(
            message.subject,
            f'Asignado a sesión – {self.slot.date:%Y-%m-%d} {self.slot.block}',
        )
        self.assertIn(f'\nAlumno: {expected}\n', message.body)
        self.assertIn(f'Aeronave: {self.slot.aircraft.registration}\n', message.body)

    def test_assignment_email_includes_student_full_name(self):
        self.slot.student = UserFactory(first_name='María', last_name='Pérez')
        self.slot.save()
        self.assert_student_line('María Pérez')

    def test_assignment_email_without_student(self):
        self.assert_student_line('no asignado')

    def test_assignment_email_with_blank_student_name(self):
        self.slot.student = UserFactory(first_name=' ', last_name=' ')
        self.slot.save()
        self.assert_student_line('no asignado')

    def test_assignment_email_with_partial_student_name(self):
        self.slot.student = UserFactory(first_name='María', last_name='')
        self.slot.save()
        self.assert_student_line('María')


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
