from datetime import date, timedelta

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from accounts.models import InstructorProfile, StaffProfile, StudentProfile, User
from prod.forms import ProductionFilterForm


class ProductionPanelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            national_id=9000001,
            password='test-password',
            role='STAFF',
            first_name='School',
            last_name='Owner',
        )
        StaffProfile.objects.create(user=self.user, position='Propietario')
        self.url = reverse('prod:production_panel')

    def grant_permission(self):
        permission = Permission.objects.get(codename='can_view_production')
        self.user.user_permissions.add(permission)

    def test_login_and_permission_are_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_owner_can_open_panel(self):
        self.grant_permission()
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Panel de Producción')
        self.assertContains(response, 'Generar reporte')
        self.assertEqual(
            response.context['form'].initial['start_date'],
            date.today() - timedelta(days=30),
        )

    def test_valid_dates_render_report(self):
        self.grant_permission()
        self.client.force_login(self.user)

        response = self.client.get(
            self.url,
            {'start_date': '2026-06-05', 'end_date': '2026-08-13'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['report'])
        self.assertEqual(
            response.context['report'].filters.start_date,
            date(2026, 6, 5),
        )
        self.assertContains(response, 'Producción por aeronave')

    def test_reversed_dates_show_validation_error(self):
        self.grant_permission()
        self.client.force_login(self.user)

        response = self.client.get(
            self.url,
            {'start_date': '2026-08-13', 'end_date': '2026-06-05'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['report'])
        self.assertContains(
            response,
            'La fecha inicial no puede ser posterior a la fecha final.',
        )

    def test_people_filters_only_offer_flying_students_and_instructors(self):
        flying_student = self.create_user('flying-student', 9000010, 'STUDENT')
        ground_student = self.create_user('ground-student', 9000011, 'STUDENT')
        flying_student_profile = StudentProfile.objects.create(
            user=flying_student,
            student_phase=StudentProfile.FLYING,
            student_age=18,
        )
        StudentProfile.objects.create(
            user=ground_student,
            student_phase=StudentProfile.GROUND,
            student_age=18,
        )

        flying_instructor = self.create_user('flying-instructor', 9000020, 'INSTRUCTOR')
        dual_instructor = self.create_user('dual-instructor', 9000021, 'INSTRUCTOR')
        ground_instructor = self.create_user('ground-instructor', 9000022, 'INSTRUCTOR')
        flying_profile = InstructorProfile.objects.create(
            user=flying_instructor,
            instructor_type=InstructorProfile.FLYING,
        )
        dual_profile = InstructorProfile.objects.create(
            user=dual_instructor,
            instructor_type=InstructorProfile.DUAL,
        )
        InstructorProfile.objects.create(
            user=ground_instructor,
            instructor_type=InstructorProfile.GROUND,
        )

        form = ProductionFilterForm()

        self.assertEqual(form.fields['aircraft'].empty_label, 'All - Todos')
        self.assertEqual(form.fields['simulators'].empty_label, 'All - Todos')
        self.assertEqual(form.fields['instructors'].empty_label, 'All - Todos')
        self.assertEqual(form.fields['students'].empty_label, 'All - Todos')

        self.assertEqual(
            set(form.fields['students'].queryset.values_list('pk', flat=True)),
            {flying_student_profile.pk},
        )
        self.assertEqual(
            set(form.fields['instructors'].queryset.values_list('pk', flat=True)),
            {flying_profile.pk, dual_profile.pk},
        )

    @staticmethod
    def create_user(username, national_id, role):
        return User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            national_id=national_id,
            password='test-password',
            role=role,
            first_name=username,
            last_name='Test',
        )
