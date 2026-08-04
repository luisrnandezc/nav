from decimal import Decimal

from django.contrib import admin
from django.core.exceptions import FieldDoesNotExist
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import InstructorProfile
from fleet.models import Aircraft
from fms.admin import ExternalFlightEvaluationAdmin
from fms.forms import ExternalFlightEvaluationForm
from fms.models import ExternalFlightEvaluation
from fms.views import get_evaluation_and_template

from .factories import StudentProfileFactory, UserFactory


class ExternalEvaluationTestMixin:
    def setUp(self):
        self.student = UserFactory(
            first_name='Alumno',
            last_name='NAV',
            role='STUDENT',
        )
        self.student_profile = StudentProfileFactory(
            user=self.student,
            flight_hours=Decimal('42.0'),
            nav_flight_hours=Decimal('18.0'),
            balance=Decimal('975.00'),
        )
        self.instructor = UserFactory(
            first_name='Instructor',
            last_name='NAV',
            role='INSTRUCTOR',
        )
        InstructorProfile.objects.create(
            user=self.instructor,
            instructor_type='VUELO',
            instructor_license_type='PCA',
        )
        self.school_aircraft, _ = Aircraft.objects.get_or_create(
            registration='YV204E',
            defaults={
                'manufacturer': 'Piper',
                'model': 'PA-28',
                'serial_number': 'TEST-EXT-001',
                'year_manufactured': 1980,
            },
        )
        self.school_aircraft.total_hours = Decimal('1500.0')
        self.school_aircraft.save(update_fields=['total_hours'])

    def valid_form_data(self, **overrides):
        data = {
            'instructor_id': self.instructor.national_id,
            'instructor_first_name': self.instructor.first_name,
            'instructor_last_name': self.instructor.last_name,
            'instructor_license_type': 'PCA',
            'instructor_license_number': self.instructor.national_id,
            'student_id': self.student.national_id,
            'student_first_name': self.student.first_name,
            'student_last_name': self.student.last_name,
            'student_license_type': 'PPA',
            'course_type': 'PCA-P',
            'evaluation_type': 'MULTIMOTOR',
            'flight_rules': 'VFR',
            'solo_flight': 'NO',
            'session_number': '1',
            'session_letter': '',
            'session_date': timezone.localdate().isoformat(),
            'accumulated_flight_hours': '42.0',
            'initial_hourmeter': '100.0',
            'final_hourmeter': '101.4',
            'fuel_consumed': '20.0',
            'aircraft': 'yv1234',
            'session_grade': 'S',
            'comments': 'Evaluación externa completada satisfactoriamente.',
        }
        data.update({name: 'NE' for name in ExternalFlightEvaluationForm.GRADE_FIELDS})
        data.update({'pre_1': 'SS', 'to_2': 'S', 'inst_3': 'NS'})
        data.update(overrides)
        return data

    def create_evaluation(self, **overrides):
        form = ExternalFlightEvaluationForm(
            data=self.valid_form_data(**overrides),
            user=self.instructor,
        )
        self.assertTrue(form.is_valid(), msg=form.errors.as_json())
        return form.save()


class ExternalFlightEvaluationModelTests(ExternalEvaluationTestMixin, TestCase):
    def test_form_stores_documentary_fields_and_all_grades(self):
        evaluation = self.create_evaluation()

        self.assertEqual(evaluation.aircraft_registration, 'YV1234')
        self.assertEqual(evaluation.session_flight_hours, Decimal('1.4'))
        self.assertEqual(len(evaluation.grades), len(ExternalFlightEvaluationForm.GRADE_FIELDS))
        self.assertEqual(evaluation.grades['pre_1'], 'SS')
        self.assertEqual(evaluation.grades['to_2'], 'S')
        self.assertEqual(evaluation.grades['inst_3'], 'NS')

    def test_grade_attributes_read_from_json_and_default_to_ne(self):
        evaluation = self.create_evaluation()
        evaluation.grades.pop('pre_2')

        self.assertEqual(evaluation.pre_1, 'SS')
        self.assertEqual(evaluation.pre_2, 'NE')

    def test_create_and_delete_do_not_mutate_student_or_fleet(self):
        initial_student_values = (
            self.student_profile.flight_hours,
            self.student_profile.nav_flight_hours,
            self.student_profile.balance,
        )
        initial_aircraft_hours = self.school_aircraft.total_hours

        evaluation = self.create_evaluation()
        evaluation.delete()

        self.student_profile.refresh_from_db()
        self.school_aircraft.refresh_from_db()
        self.assertEqual(
            (
                self.student_profile.flight_hours,
                self.student_profile.nav_flight_hours,
                self.student_profile.balance,
            ),
            initial_student_values,
        )
        self.assertEqual(self.school_aircraft.total_hours, initial_aircraft_hours)

    def test_model_has_no_aircraft_or_aura_relationships(self):
        for field_name in ('aircraft', 'aura_processed', 'aura_review'):
            with self.assertRaises(FieldDoesNotExist):
                ExternalFlightEvaluation._meta.get_field(field_name)

    def test_form_rejects_invalid_hourmeter_range(self):
        form = ExternalFlightEvaluationForm(
            data=self.valid_form_data(initial_hourmeter='101.0', final_hourmeter='100.0'),
            user=self.instructor,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('horómetro final no puede ser menor', str(form.non_field_errors()))

    def test_form_rejects_unknown_student(self):
        form = ExternalFlightEvaluationForm(
            data=self.valid_form_data(student_id='99999999'),
            user=self.instructor,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('No se encontró un perfil de estudiante', str(form.non_field_errors()))

    def test_evaluation_type_options_are_multimotor_and_other(self):
        self.assertEqual(
            list(ExternalFlightEvaluation.EVALUATION_TYPE_CHOICES),
            [('MULTIMOTOR', 'Multimotor'), ('OTRO', 'Otro')],
        )


class ExternalFlightEvaluationViewTests(ExternalEvaluationTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.instructor)

    def test_submission_creates_record_and_redirects_to_pdf_waiting_page(self):
        response = self.client.post(
            reverse('fms:external_flight_evaluation'),
            data=self.valid_form_data(),
        )

        evaluation = ExternalFlightEvaluation.objects.get()
        self.assertRedirects(
            response,
            reverse(
                'fms:pdf_download_waiting_page',
                kwargs={'form_type': 'external', 'evaluation_id': evaluation.id},
            ),
            fetch_redirect_response=False,
        )

    def test_external_registry_and_detail_show_documentary_information(self):
        evaluation = self.create_evaluation(evaluation_type='OTRO', aircraft='YV5678')

        registry = self.client.get(reverse('fms:external_evaluations'))
        self.assertContains(registry, 'Alumno NAV')
        self.assertContains(registry, 'YV5678')
        self.assertContains(registry, 'Otro')

        detail = self.client.get(
            reverse(
                'fms:session_detail',
                kwargs={'form_type': 'external', 'evaluation_id': evaluation.id},
            )
        )
        self.assertContains(detail, 'Evaluación externa')
        self.assertContains(detail, 'YV5678')
        self.assertContains(detail, 'Descargar PDF')

    def test_external_routes_require_login(self):
        self.client.logout()

        for route_name in ('external_flight_evaluation', 'external_evaluations'):
            response = self.client.get(reverse(f'fms:{route_name}'))
            self.assertEqual(response.status_code, 302)

    def test_pdf_uses_external_template_title_and_blank_hours_heading(self):
        evaluation = self.create_evaluation()
        resolved, template_name = get_evaluation_and_template('external', evaluation.id)
        html = render_to_string(
            template_name,
            {'evaluation': resolved, 'logo_path': ''},
        )

        self.assertEqual(resolved, evaluation)
        self.assertEqual(template_name, 'fms/pdf_120_170.html')
        self.assertIn('FORMULARIO DE PRUEBAS DE PERICIA - MULTIMOTOR', html)
        self.assertNotIn('40-150 Hrs', html)
        self.assertIn('Matrícula de aeronave: YV1234', html)


class ExternalFlightEvaluationAdminTests(ExternalEvaluationTestMixin, TestCase):
    def test_admin_is_registered_with_pdf_action_and_expected_columns(self):
        model_admin = admin.site._registry[ExternalFlightEvaluation]

        self.assertIsInstance(model_admin, ExternalFlightEvaluationAdmin)
        self.assertIn('aircraft_display', model_admin.list_display)
        self.assertIn('session_hours', model_admin.list_display)
        self.assertIn('generate_pdf', model_admin.actions)
        self.assertEqual(model_admin.aircraft_display.short_description, 'Aeronave')
        self.assertEqual(model_admin.session_hours.short_description, 'Horas')

    def test_admin_exposes_individual_json_grades_as_read_only_fields(self):
        evaluation = self.create_evaluation()
        model_admin = admin.site._registry[ExternalFlightEvaluation]

        self.assertIn('grade_pre_1', model_admin.get_readonly_fields(None, evaluation))
        self.assertEqual(model_admin.grade_pre_1(evaluation), 'SS')
        self.assertEqual(model_admin.grade_pre_2(evaluation), 'NE')
