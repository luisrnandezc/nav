"""Tests for grading helpers and related model validation."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import InstructorProfile, StudentProfile, User

from .grading import (
    RECOVERY_PASSING_GRADE,
    STANDARD_PASSING_GRADE,
    final_weighted_grade,
    student_passed_final,
)
from .models import CourseType, StudentGrade, SubjectEdition, SubjectType


class GradingTestCase(TestCase):
    """Shared fixtures: course, subject type, instructor, student, subject edition."""

    _national_id_seq = 10_250_000

    @classmethod
    def _next_national_id(cls) -> int:
        cls._national_id_seq += 1
        return cls._national_id_seq

    def setUp(self):
        self.course_type = CourseType.objects.create(
            code='PPA-T',
            name='Piloto Privado Avión Teórico',
            credit_hours=10,
        )
        self.subject_type = SubjectType.objects.create(
            course_type=self.course_type,
            code='PPA-AER-I',
            name='PPA - Aeronáutica I',
            credit_hours=2,
        )
        self.instructor = User.objects.create_user(
            username='inst_grading',
            email='inst_grading@test.nav',
            national_id=self._next_national_id(),
            password='x',
            role=User.Role.INSTRUCTOR,
            first_name='Ann',
            last_name='Instructor',
        )
        InstructorProfile.objects.create(
            user=self.instructor,
            instructor_type=InstructorProfile.GROUND,
        )
        self.student = User.objects.create_user(
            username='stu_grading',
            email='stu_grading@test.nav',
            national_id=self._next_national_id(),
            password='x',
            role=User.Role.STUDENT,
            first_name='Bob',
            last_name='Student',
        )
        StudentProfile.objects.create(
            user=self.student,
            student_age=20,
        )
        today = timezone.now().date()
        self.edition_theory_only = SubjectEdition(
            subject_type=self.subject_type,
            instructor=self.instructor,
            time_slot='M',
            start_date=today,
            end_date=today,
            start_time=timezone.datetime.strptime('09:00', '%H:%M').time(),
            end_time=timezone.datetime.strptime('12:00', '%H:%M').time(),
            theory_weight=Decimal('1'),
            practical_weight=Decimal('0'),
        )
        self.edition_theory_only.save()
        self.edition_theory_only.students.add(self.student)

        self.edition_mixed = SubjectEdition(
            subject_type=self.subject_type,
            instructor=self.instructor,
            time_slot='T',
            start_date=today,
            end_date=today,
            start_time=timezone.datetime.strptime('09:00', '%H:%M').time(),
            end_time=timezone.datetime.strptime('12:00', '%H:%M').time(),
            theory_weight=Decimal('0.8'),
            practical_weight=Decimal('0.2'),
        )
        self.edition_mixed.save()
        self.edition_mixed.students.add(self.student)

    def _add_grade(self, edition, component, grade, test_type='STANDARD'):
        return StudentGrade.objects.create(
            subject_edition=edition,
            student=self.student,
            instructor=self.instructor,
            component=component,
            grade=Decimal(str(grade)),
            test_type=test_type,
        )


class FinalWeightedGradeTests(GradingTestCase):
    def test_theory_only_full_weight_returns_theory_standard(self):
        self._add_grade(self.edition_theory_only, 'theory', 85)
        result = final_weighted_grade(self.edition_theory_only, self.student.pk)
        self.assertEqual(result, Decimal('85.0'))

    def test_theory_only_missing_standard_returns_none(self):
        self.assertIsNone(final_weighted_grade(self.edition_theory_only, self.student.pk))

    def test_theory_only_recovery_does_not_count_toward_final(self):
        self._add_grade(self.edition_theory_only, 'theory', 50, test_type='RECOVERY')
        self.assertIsNone(final_weighted_grade(self.edition_theory_only, self.student.pk))

    def test_mixed_weights_computes_weighted_sum(self):
        self._add_grade(self.edition_mixed, 'theory', 80)
        self._add_grade(self.edition_mixed, 'practical', 100)
        result = final_weighted_grade(self.edition_mixed, self.student.pk)
        self.assertEqual(result, Decimal('84.0'))

    def test_mixed_missing_practical_returns_none(self):
        self._add_grade(self.edition_mixed, 'theory', 90)
        self.assertIsNone(final_weighted_grade(self.edition_mixed, self.student.pk))

    def test_mixed_missing_theory_returns_none(self):
        self._add_grade(self.edition_mixed, 'practical', 90)
        self.assertIsNone(final_weighted_grade(self.edition_mixed, self.student.pk))

    def test_custom_weight_split_computes_weighted_sum(self):
        self.edition_mixed.theory_weight = Decimal('0.7')
        self.edition_mixed.practical_weight = Decimal('0.3')
        self.edition_mixed.save()
        self._add_grade(self.edition_mixed, 'theory', 80)
        self._add_grade(self.edition_mixed, 'practical', 100)
        self.assertEqual(final_weighted_grade(self.edition_mixed, self.student.pk), Decimal('86.0'))


class SubjectEditionWeightPolicyTests(GradingTestCase):
    def test_arbitrary_positive_split_passes_validation(self):
        self.edition_mixed.theory_weight = Decimal('0.7')
        self.edition_mixed.practical_weight = Decimal('0.3')
        self.edition_mixed.full_clean()

    def test_weights_must_sum_to_one(self):
        self.edition_mixed.theory_weight = Decimal('0.6')
        self.edition_mixed.practical_weight = Decimal('0.3')
        with self.assertRaises(ValidationError):
            self.edition_mixed.full_clean()


class StudentPassedFinalTests(GradingTestCase):
    def test_passes_when_final_at_least_standard_threshold(self):
        self._add_grade(self.edition_theory_only, 'theory', STANDARD_PASSING_GRADE)
        self.assertTrue(student_passed_final(self.edition_theory_only, self.student.pk))

    def test_fails_when_below_threshold_and_no_recovery(self):
        self._add_grade(self.edition_theory_only, 'theory', Decimal('79'))
        self.assertFalse(student_passed_final(self.edition_theory_only, self.student.pk))

    def test_passes_via_recovery_when_final_below_but_theory_recovery_enough(self):
        self._add_grade(self.edition_theory_only, 'theory', Decimal('79'))
        self._add_grade(self.edition_theory_only, 'theory', RECOVERY_PASSING_GRADE, test_type='RECOVERY')
        self.assertTrue(student_passed_final(self.edition_theory_only, self.student.pk))

    def test_fails_recovery_below_ninety(self):
        self._add_grade(self.edition_theory_only, 'theory', Decimal('79'))
        self._add_grade(self.edition_theory_only, 'theory', Decimal('89'), test_type='RECOVERY')
        self.assertFalse(student_passed_final(self.edition_theory_only, self.student.pk))

    def test_incomplete_final_returns_none(self):
        self.assertIsNone(student_passed_final(self.edition_theory_only, self.student.pk))

    def test_mixed_passes_on_weighted_final_without_recovery(self):
        self._add_grade(self.edition_mixed, 'theory', 75)
        self._add_grade(self.edition_mixed, 'practical', 100)
        self.assertTrue(student_passed_final(self.edition_mixed, self.student.pk))


class StudentGradeValidationTests(GradingTestCase):
    def test_practical_not_allowed_when_edition_has_no_practical_weight(self):
        with self.assertRaises(ValidationError):
            StudentGrade(
                subject_edition=self.edition_theory_only,
                student=self.student,
                instructor=self.instructor,
                component='practical',
                grade=Decimal('90'),
            ).save()

    def test_recovery_only_on_theory(self):
        with self.assertRaises(ValidationError):
            StudentGrade(
                subject_edition=self.edition_mixed,
                student=self.student,
                instructor=self.instructor,
                component='practical',
                grade=Decimal('90'),
                test_type='RECOVERY',
            ).save()

    def test_student_must_be_enrolled(self):
        other = User.objects.create_user(
            username='other_stu',
            email='other@test.nav',
            national_id=GradingTestCase._next_national_id(),
            password='x',
            role=User.Role.STUDENT,
            first_name='O',
            last_name='Other',
        )
        StudentProfile.objects.create(user=other, student_age=21)
        with self.assertRaises(ValidationError):
            StudentGrade(
                subject_edition=self.edition_theory_only,
                student=other,
                instructor=self.instructor,
                component='theory',
                grade=Decimal('80'),
            ).save()


class StudentGradePassedPropertyTests(GradingTestCase):
    def test_standard_uses_eighty_threshold(self):
        g = self._add_grade(self.edition_theory_only, 'theory', 80)
        self.assertTrue(g.passed)
        g.grade = Decimal('79.9')
        g.save()
        self.assertFalse(g.passed)

    def test_recovery_uses_ninety_threshold(self):
        g = self._add_grade(self.edition_theory_only, 'theory', 90, test_type='RECOVERY')
        self.assertTrue(g.passed)
        g.grade = Decimal('89.9')
        g.save()
        self.assertFalse(g.passed)
