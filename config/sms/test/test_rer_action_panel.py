from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from sms.test.factories import (
    MitigationActionEvidenceFactory,
    MitigationActionFactory,
    RiskEvaluationReportFactory,
    RiskFactory,
    StaffUserFactory,
    VoluntaryHazardReportFactory,
)


class TestRERActionPanel(TestCase):
    def setUp(self):
        self.user = StaffUserFactory(is_staff=True, is_superuser=True)
        self.client.force_login(self.user)
        self.report = VoluntaryHazardReportFactory(is_processed=True)
        self.risk = RiskFactory(
            report=self.report,
            description='Pérdida de separación operacional',
            pre_evaluation_severity='B',
            pre_evaluation_probability='4',
            post_evaluation_severity='B',
            post_evaluation_probability='2',
            post_evaluation_justification='Propuesta original de SARA.',
        )
        self.action = MitigationActionFactory(
            risk=self.risk,
            responsible=self.user,
            description='Aplicar una verificación adicional.',
        )
        MitigationActionEvidenceFactory(
            mitigation_action=self.action,
            description='Registro firmado de la verificación.',
        )
        self.rer = RiskEvaluationReportFactory(
            report=self.report,
            selected_risk=self.risk,
            analysis_status='READY_FOR_REVIEW',
        )
        self.url = reverse('sms:rer_action_panel', args=[self.rer.id])

    def form_data(self, *, justification='Justificación revisada por SMS.'):
        return {
            'risks-TOTAL_FORMS': '1',
            'risks-INITIAL_FORMS': '1',
            'risks-MIN_NUM_FORMS': '0',
            'risks-MAX_NUM_FORMS': '1000',
            'risks-0-id': str(self.risk.id),
            'risks-0-post_evaluation_severity': 'C',
            'risks-0-post_evaluation_probability': '1',
            'risks-0-post_evaluation_justification': justification,
        }

    def test_action_panel_shows_sara_result_and_mitigation_context(self):
        response = self.client.get(self.url)

        assert response.status_code == 200
        self.assertContains(response, self.risk.description)
        self.assertContains(response, self.action.description)
        self.assertContains(response, self.action.evidence.description)
        self.assertContains(response, self.risk.post_evaluation_justification)

    def test_approval_updates_risk_and_marks_rer_reviewed(self):
        response = self.client.post(self.url, self.form_data())

        assert response.status_code == 302
        assert response.url == reverse('sms:rer_dashboard')

        self.risk.refresh_from_db()
        self.rer.refresh_from_db()
        assert self.risk.post_evaluation_severity == 'C'
        assert self.risk.post_evaluation_probability == '1'
        assert self.risk.post_evaluation_justification == 'Justificación revisada por SMS.'
        assert self.rer.analysis_status == 'REVIEWED'
        assert self.rer.reviewed_by == self.user
        assert self.rer.reviewed_at is not None

    def test_justification_is_required_for_approval(self):
        response = self.client.post(self.url, self.form_data(justification=''))

        assert response.status_code == 200
        self.rer.refresh_from_db()
        assert self.rer.analysis_status == 'READY_FOR_REVIEW'
        self.assertContains(response, 'Este campo es obligatorio')

    def test_rer_in_another_status_cannot_be_reviewed(self):
        self.rer.analysis_status = 'PENDING'
        self.rer.save(update_fields=['analysis_status'])

        response = self.client.get(self.url)

        assert response.status_code == 302
        assert response.url == reverse('sms:rer_dashboard')

    def test_user_without_sms_permission_cannot_open_action_panel(self):
        user_without_permission = StaffUserFactory(
            is_staff=True,
            is_superuser=False,
        )
        assert not user_without_permission.has_perm('accounts.can_manage_sms')
        self.client.force_login(user_without_permission)

        response = self.client.get(self.url)

        assert response.status_code == 302
        assert response.url == reverse('sms:rer_dashboard')

    def test_user_without_sms_permission_cannot_approve_rer(self):
        user_without_permission = StaffUserFactory(
            is_staff=True,
            is_superuser=False,
        )
        assert not user_without_permission.has_perm('accounts.can_manage_sms')
        self.client.force_login(user_without_permission)

        response = self.client.post(self.url, self.form_data())

        assert response.status_code == 302
        assert response.url == reverse('sms:rer_dashboard')
        self.rer.refresh_from_db()
        self.risk.refresh_from_db()
        assert self.rer.analysis_status == 'READY_FOR_REVIEW'
        assert self.rer.reviewed_by is None
        assert self.rer.reviewed_at is None
        assert self.risk.post_evaluation_severity == 'B'
        assert self.risk.post_evaluation_probability == '2'

    def test_pending_rer_cannot_be_approved(self):
        self.rer.analysis_status = 'PENDING'
        self.rer.save(update_fields=['analysis_status'])

        response = self.client.post(self.url, self.form_data())

        assert response.status_code == 302
        assert response.url == reverse('sms:rer_dashboard')
        self.rer.refresh_from_db()
        self.risk.refresh_from_db()
        assert self.rer.analysis_status == 'PENDING'
        assert self.rer.reviewed_by is None
        assert self.risk.post_evaluation_severity == 'B'
        assert self.risk.post_evaluation_probability == '2'

    def test_reviewed_rer_cannot_be_approved_twice(self):
        self.rer.analysis_status = 'REVIEWED'
        self.rer.reviewed_by = self.user
        self.rer.save(update_fields=['analysis_status', 'reviewed_by'])

        response = self.client.post(self.url, self.form_data())

        assert response.status_code == 302
        assert response.url == reverse('sms:rer_dashboard')
        self.rer.refresh_from_db()
        self.risk.refresh_from_db()
        assert self.rer.analysis_status == 'REVIEWED'
        assert self.rer.reviewed_by == self.user
        assert self.risk.post_evaluation_severity == 'B'
        assert self.risk.post_evaluation_probability == '2'

    def test_reviewed_rer_is_displayed_as_read_only(self):
        self.rer.analysis_status = 'REVIEWED'
        self.rer.reviewed_by = self.user
        self.rer.reviewed_at = timezone.now()
        self.rer.save(update_fields=[
            'analysis_status',
            'reviewed_by',
            'reviewed_at',
        ])

        response = self.client.get(self.url)

        assert response.status_code == 200
        assert response.context['is_read_only'] is True
        self.assertContains(response, self.risk.description)
        self.assertContains(response, self.risk.post_evaluation_justification)
        self.assertContains(response, self.user.get_full_name())
        self.assertNotContains(response, 'Aprobar RER')
        self.assertNotContains(response, '<form')

    def test_form_cannot_update_risk_from_another_report(self):
        unrelated_risk = RiskFactory(
            post_evaluation_severity='D',
            post_evaluation_probability='4',
            post_evaluation_justification='Evaluación de otro reporte.',
        )
        data = self.form_data()
        data['risks-0-id'] = str(unrelated_risk.id)

        response = self.client.post(self.url, data)

        assert response.status_code == 200
        self.rer.refresh_from_db()
        self.risk.refresh_from_db()
        unrelated_risk.refresh_from_db()
        assert self.rer.analysis_status == 'READY_FOR_REVIEW'
        assert self.risk.post_evaluation_severity == 'B'
        assert self.risk.post_evaluation_probability == '2'
        assert unrelated_risk.post_evaluation_severity == 'D'
        assert unrelated_risk.post_evaluation_probability == '4'
