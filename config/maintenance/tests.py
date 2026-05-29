from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from accounts.models import StaffProfile, User
from fleet.models import Aircraft
from fms.models import DiscrepancyReport


class DiscrepancyReportsPanelTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username='maintenance',
            email='maintenance@example.com',
            national_id=1234567,
            password='password',
            first_name='Maintenance',
            last_name='Staff',
            role='STAFF',
        )
        StaffProfile.objects.create(user=self.staff)

        self.aircraft = Aircraft.objects.create(
            manufacturer='Cessna',
            model='172',
            registration='YV001',
            serial_number='SN001',
            year_manufactured=2000,
        )

        self.pending_report = DiscrepancyReport.objects.create(
            aircraft=self.aircraft,
            reportee_first_name='Ana',
            reportee_last_name='Perez',
            discrepancy_type='ENGINE',
            discrepancy_description='Engine vibration reported during climb.',
            status='PENDING',
        )
        self.completed_report = DiscrepancyReport.objects.create(
            aircraft=self.aircraft,
            reportee_first_name='Luis',
            reportee_last_name='Rojas',
            discrepancy_type='AVIONICS',
            discrepancy_description='Resolved avionics discrepancy.',
            status='COMPLETED',
        )
        self.url = reverse('maintenance:discrepancy_reports_panel')

    def test_requires_discrepancy_permission(self):
        self.client.login(username='maintenance', password='password')

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('dashboard:dashboard'))

    def test_panel_defaults_to_current_reports(self):
        permission = Permission.objects.get(codename='view_discrepancyreport')
        self.staff.user_permissions.add(permission)
        self.client.login(username='maintenance', password='password')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Engine vibration reported during climb.')
        self.assertNotContains(response, 'Resolved avionics discrepancy.')

    def test_status_filter_can_show_completed_reports(self):
        permission = Permission.objects.get(codename='view_discrepancyreport')
        self.staff.user_permissions.add(permission)
        self.client.login(username='maintenance', password='password')

        response = self.client.get(self.url, {'status': 'COMPLETED'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resolved avionics discrepancy.')
        self.assertNotContains(response, 'Engine vibration reported during climb.')
