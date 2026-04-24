from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import InstructorProfile, StudentProfile, User
from academic.grading import (
    effective_grade_for_component,
    final_weighted_grade,
    grading_components_weight_sum,
    student_passed_final,
)
from academic.models import (
    CourseType,
    StudentGrade,
    SubjectEdition,
    SubjectEditionGradingComponent,
    SubjectType,
)


def _make_instructor(username='inst1', national_id=2000001):
    u = User.objects.create(
        username=username,
        email=f'{username}@test.com',
        national_id=national_id,
        role='INSTRUCTOR',
        first_name='Ann',
        last_name='Instructor',
    )
    InstructorProfile.objects.create(user=u, instructor_type='TIERRA')
    return u


def _make_student(username='stu1', national_id=3000001):
    u = User.objects.create(
        username=username,
        email=f'{username}@test.com',
        national_id=national_id,
        role='STUDENT',
        first_name='Sam',
        last_name='Student',
    )
    StudentProfile.objects.create(user=u, student_age=20, balance=1000)
    return u


class GradingComponentsModelTest(TestCase):
    def setUp(self):
        self.course = CourseType.objects.create(
            code='PPA-T',
            name='Piloto Privado Avión Teórico',
        )
        self.subject_type = SubjectType.objects.create(
            course_type=self.course,
            code='PPA-NAV',
            name='PPA - Navegación Visual',
        )
        self.instructor = _make_instructor()
        self.student = _make_student()
        self.edition = SubjectEdition.objects.create(
            subject_type=self.subject_type,
            instructor=self.instructor,
            time_slot='M',
        )
        self.edition.students.add(self.student)
        self.theory = SubjectEditionGradingComponent.objects.create(
            subject_edition=self.edition,
            code='theory',
            kind='THEORY',
            label='Examen teórico',
            weight=Decimal('0.7'),
            order=0,
        )
        self.practical = SubjectEditionGradingComponent.objects.create(
            subject_edition=self.edition,
            code='practical',
            kind='PRACTICAL',
            label='Evaluación práctica',
            weight=Decimal('0.3'),
            order=1,
        )

    def test_weight_sum_helper(self):
        self.assertEqual(grading_components_weight_sum(self.edition), Decimal('1'))

    def test_final_weighted_grade(self):
        StudentGrade.objects.create(
            student=self.student,
            instructor=self.instructor,
            subject_edition=self.edition,
            component=self.theory,
            grade=Decimal('80.0'),
            test_type='STANDARD',
        )
        StudentGrade.objects.create(
            student=self.student,
            instructor=self.instructor,
            subject_edition=self.edition,
            component=self.practical,
            grade=Decimal('90.0'),
            test_type='STANDARD',
        )
        final = final_weighted_grade(self.edition, self.student.id)
        self.assertEqual(final, Decimal('83.0'))

    def test_effective_grade_uses_max_of_standard_and_recovery(self):
        StudentGrade.objects.create(
            student=self.student,
            instructor=self.instructor,
            subject_edition=self.edition,
            component=self.theory,
            grade=Decimal('70.0'),
            test_type='STANDARD',
        )
        StudentGrade.objects.create(
            student=self.student,
            instructor=self.instructor,
            subject_edition=self.edition,
            component=self.theory,
            grade=Decimal('85.0'),
            test_type='RECOVERY',
        )
        eg = effective_grade_for_component(self.student.id, self.theory)
        self.assertEqual(eg, Decimal('85.0'))

    def test_student_grade_clean_rejects_mismatched_component_edition(self):
        other_edition = SubjectEdition.objects.create(
            subject_type=self.subject_type,
            instructor=self.instructor,
            time_slot='T',
        )
        other_edition.students.add(self.student)
        other_comp = SubjectEditionGradingComponent.objects.create(
            subject_edition=other_edition,
            code='theory',
            kind='THEORY',
            label='Teórico',
            weight=Decimal('1.0'),
            order=0,
        )
        SubjectEditionGradingComponent.objects.create(
            subject_edition=other_edition,
            code='practical',
            kind='PRACTICAL',
            label='Práctica',
            weight=Decimal('0'),
            order=1,
        )
        g = StudentGrade(
            student=self.student,
            instructor=self.instructor,
            subject_edition=self.edition,
            component=other_comp,
            grade=Decimal('80.0'),
            test_type='STANDARD',
        )
        with self.assertRaises(ValidationError):
            g.full_clean()

    def test_student_grade_clean_requires_weights_sum_to_one(self):
        self.practical.weight = Decimal('0.05')
        self.practical.save()
        self.theory.weight = Decimal('0.9')
        self.theory.save()
        try:
            g = StudentGrade(
                student=self.student,
                instructor=self.instructor,
                subject_edition=self.edition,
                component=self.theory,
                grade=Decimal('80.0'),
                test_type='STANDARD',
            )
            with self.assertRaises(ValidationError):
                g.full_clean()
        finally:
            self.theory.weight = Decimal('0.7')
            self.theory.save()
            self.practical.weight = Decimal('0.3')
            self.practical.save()

    def test_final_weighted_grade_ignores_zero_weight_practical(self):
        self.practical.weight = Decimal('0')
        self.practical.save()
        self.theory.weight = Decimal('1.0')
        self.theory.save()
        try:
            StudentGrade.objects.create(
                student=self.student,
                instructor=self.instructor,
                subject_edition=self.edition,
                component=self.theory,
                grade=Decimal('80.0'),
                test_type='STANDARD',
            )
            final = final_weighted_grade(self.edition, self.student.id)
            self.assertEqual(final, Decimal('80.0'))
        finally:
            self.theory.weight = Decimal('0.7')
            self.theory.save()
            self.practical.weight = Decimal('0.3')
            self.practical.save()

    def test_invalid_component_code_rejected(self):
        bad = SubjectEditionGradingComponent(
            subject_edition=self.edition,
            code='oral',
            kind='THEORY',
            label='Oral',
            weight=Decimal('0.01'),
            order=2,
        )
        with self.assertRaises(ValidationError):
            bad.full_clean()

    def test_cannot_save_component_if_total_weight_would_exceed_one(self):
        try:
            self.theory.weight = Decimal('0.6')
            self.theory.save()
            self.practical.weight = Decimal('0.6')
            with self.assertRaises(ValidationError):
                self.practical.save()
        finally:
            self.theory.weight = Decimal('0.7')
            self.theory.save()
            self.practical.weight = Decimal('0.3')
            self.practical.save()

    def test_validate_weight_total_classmethod_batch(self):
        with self.assertRaises(ValidationError):
            SubjectEditionGradingComponent.validate_weight_total(
                [Decimal('0.6'), Decimal('0.6')]
            )
        SubjectEditionGradingComponent.validate_weight_total(
            [Decimal('0.6'), Decimal('0.4')]
        )

    def test_student_passed_final_uses_recovery_threshold_when_recovery_exists(self):
        StudentGrade.objects.create(
            student=self.student,
            instructor=self.instructor,
            subject_edition=self.edition,
            component=self.theory,
            grade=Decimal('100.0'),
            test_type='STANDARD',
        )
        StudentGrade.objects.create(
            student=self.student,
            instructor=self.instructor,
            subject_edition=self.edition,
            component=self.practical,
            grade=Decimal('100.0'),
            test_type='RECOVERY',
        )
        self.assertTrue(student_passed_final(self.edition, self.student.id))
