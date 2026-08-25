from datetime import date, timedelta
from decimal import Decimal

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
        self.assertContains(response, 'Horas de Línea de Vuelo')
        self.assertContains(response, 'Ingreso Operativo de Línea de Vuelo')
        self.assertContains(response, 'Excluye evaluaciones externas y reportes de vuelo.')
        self.assertNotContains(response, 'Producción por fecha')
        self.assertNotContains(response, 'Producción por estudiante')
        self.assertIsNotNone(response.context['chart_data'])

    def test_current_flying_student_balances_are_always_visible(self):
        balances = (
            ('high-balance', 9000030, StudentProfile.FLYING, '600.00'),
            ('low-balance', 9000031, StudentProfile.FLYING, '250.00'),
            ('zero-balance', 9000032, StudentProfile.FLYING, '0.00'),
            ('negative-balance', 9000033, StudentProfile.FLYING, '-20.00'),
            ('ground-balance', 9000034, StudentProfile.GROUND, '999.00'),
        )
        flying_profiles = []
        for username, national_id, phase, balance in balances:
            student = self.create_user(username, national_id, 'STUDENT')
            profile = StudentProfile.objects.create(
                user=student,
                student_phase=phase,
                student_age=18,
                balance=Decimal(balance),
            )
            if phase == StudentProfile.FLYING:
                flying_profiles.append(profile)
        self.grant_permission()
        self.client.force_login(self.user)

        response = self.client.get(
            self.url,
            {
                'start_date': '2026-06-05',
                'end_date': '2026-08-13',
                'students': flying_profiles[0].pk,
            },
        )

        rows = {
            row['national_id']: row
            for row in response.context['student_balances']
        }
        self.assertEqual(set(rows), {9000030, 9000031, 9000032, 9000033})
        self.assertEqual(response.context['total_student_balance'], Decimal('830.00'))
        self.assertEqual(response.context['total_balance_badge'], 'badge-green')
        self.assertEqual(rows[9000030]['badge'], 'badge-green')
        self.assertEqual(rows[9000031]['badge'], 'badge-yellow')
        self.assertEqual(rows[9000032]['badge'], 'badge-yellow')
        self.assertEqual(rows[9000033]['badge'], 'badge-red')
        self.assertContains(response, 'Estatus actual de balances en LV')
        self.assertContains(response, 'Balance LV')
        self.assertContains(response, 'balance-table-scroll')
        self.assertNotContains(response, 'ground-balance')

    def test_negative_total_balance_uses_red_badge(self):
        student = self.create_user('student-in-debt', 9000040, 'STUDENT')
        StudentProfile.objects.create(
            user=student,
            student_phase=StudentProfile.FLYING,
            student_age=18,
            balance=Decimal('-50.00'),
        )
        self.grant_permission()
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.context['total_student_balance'], Decimal('-50.00'))
        self.assertEqual(response.context['total_balance_badge'], 'badge-red')

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
