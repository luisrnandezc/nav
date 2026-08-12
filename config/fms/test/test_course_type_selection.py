from django.test import TestCase
from django.urls import reverse

from academic.models import CourseEdition, CourseType
from fms.forms import (
    ExternalFlightEvaluationForm,
    FlightEvaluation0_100Form,
    FlightEvaluation100_120Form,
    FlightEvaluation120_170Form,
    SimEvaluationForm,
)
from fms.models import SimEvaluation

from .factories import StudentProfileFactory, UserFactory


class CourseTypeSelectionTests(TestCase):
    form_classes = (
        SimEvaluationForm,
        FlightEvaluation0_100Form,
        FlightEvaluation100_120Form,
        FlightEvaluation120_170Form,
        ExternalFlightEvaluationForm,
    )

    def setUp(self):
        self.course_type = CourseType.objects.create(
            code='MM-P',
            name='Multimotor práctico',
        )
        self.course_edition = CourseEdition.objects.create(
            course_type=self.course_type,
            modality='INDIVIDUAL',
            edition=1,
        )

    def test_all_evaluation_forms_include_academic_course_codes(self):
        for form_class in self.form_classes:
            with self.subTest(form=form_class.__name__):
                choices = dict(form_class().fields['course_type'].choices)
                self.assertEqual(choices['MM-P'], 'MM-P')

    def test_evaluation_forms_only_offer_academic_course_types(self):
        for form_class in self.form_classes:
            with self.subTest(form=form_class.__name__):
                choices = dict(form_class().fields['course_type'].choices)
                self.assertNotIn('PPA-P', choices)

    def test_deleted_course_type_is_removed_from_new_evaluation_forms(self):
        self.course_edition.delete()
        self.course_type.delete()

        for form_class in self.form_classes:
            with self.subTest(form=form_class.__name__):
                choices = dict(form_class().fields['course_type'].choices)
                self.assertNotIn('MM-P', choices)

    def test_existing_evaluation_keeps_deleted_course_type_when_editing(self):
        evaluation = SimEvaluation(course_type='OLD-P')
        evaluation.pk = 1

        choices = dict(
            SimEvaluationForm(instance=evaluation).fields['course_type'].choices
        )

        self.assertEqual(choices['OLD-P'], 'OLD-P')

    def test_student_lookup_returns_current_enrolled_course_code(self):
        student = UserFactory(role='STUDENT')
        StudentProfileFactory(user=student)
        self.course_edition.students.add(student)
        self.client.force_login(student)

        response = self.client.get(
            reverse('fms:get_student_data'),
            {'student_id': student.national_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['data']['course_type'], 'MM-P')
