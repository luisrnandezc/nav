from django.test import TestCase
from django.urls import reverse

from sms.forms import RiskEvaluationReportForm
from sms.models import RiskEvaluationReport
from sms.test.factories import (
    RiskEvaluationReportFactory,
    RiskFactory,
    MitigationActionEvidenceFactory,
    MitigationActionFactory,
    StaffUserFactory,
    VoluntaryHazardReportFactory,
)


def rer_form_data(report, selected_risk):
    return {
        'registration_date': report.date.isoformat(),
        'sms_user_fullname': 'Coordinador SMS',
        'dir_user_fullname': 'Director General',
        'hazard_description': 'Peligro operacional identificado.',
        'hazard_source': 'VHR',
        'hazard_type': 'ORG',
        'hazard_area': report.area,
        'selected_risk': selected_risk.id,
        'hazard_causes': 'Falta de coordinación y supervisión.',
        'defenses': 'Procedimientos y listas de verificación.',
    }


class TestRiskEvaluationReportModelForm(TestCase):
    def test_form_creates_rer_with_a_risk_from_the_report(self):
        report = VoluntaryHazardReportFactory()
        selected_risk = RiskFactory(report=report)
        form = RiskEvaluationReportForm(
            data=rer_form_data(report, selected_risk),
            report=report,
            instance=RiskEvaluationReport(report=report),
        )

        assert form.is_valid(), form.errors
        rer = form.save()
        assert rer.report_id == report.id
        assert rer.selected_risk_id == selected_risk.id

    def test_form_rejects_a_risk_from_another_report(self):
        report = VoluntaryHazardReportFactory()
        unrelated_risk = RiskFactory()
        form = RiskEvaluationReportForm(
            data=rer_form_data(report, unrelated_risk),
            report=report,
            instance=RiskEvaluationReport(report=report),
        )

        assert not form.is_valid()
        assert 'selected_risk' in form.errors

class TestRiskEvaluationReportFormView(TestCase):
    def setUp(self):
        self.user = StaffUserFactory(is_staff=True, is_superuser=True)
        self.client.force_login(self.user)
        self.report = VoluntaryHazardReportFactory(
            code='SMS-RVP-100',
            is_processed=True,
        )
        self.risk = RiskFactory(report=self.report)
        self.risk.pre_evaluation_severity = 'B'
        self.risk.pre_evaluation_probability = '3'
        self.risk.save(update_fields=[
            'pre_evaluation_severity',
            'pre_evaluation_probability',
        ])
        self.action = MitigationActionFactory(
            risk=self.risk,
            responsible=self.user,
        )
        MitigationActionEvidenceFactory(mitigation_action=self.action)
        self.url = reverse('sms:rer_form', args=[self.report.id])

    def test_post_creates_rer_pending_sara_analysis(self):
        response = self.client.post(
            self.url,
            data=rer_form_data(self.report, self.risk),
        )

        assert response.status_code == 302
        assert response.url == reverse(
            'sms:vhr_processed_panel',
            args=[self.report.id],
        )
        rer = RiskEvaluationReport.objects.get(report=self.report)
        assert rer.selected_risk_id == self.risk.id
        assert rer.analysis_status == 'PENDING'
        assert rer.analysis_error == ''
        assert rer.analysis_started_at is None
        assert rer.analysis_completed_at is None
        assert rer.reviewed_by is None
        assert rer.reviewed_at is None

    def test_sara_submission_message_appears_once_on_redirect_destination(self):
        success_message = (
            'El RER fue enviado a SARA y está pendiente de análisis.'
        )

        response = self.client.post(
            self.url,
            data=rer_form_data(self.report, self.risk),
            follow=True,
        )

        assert response.redirect_chain == [(
            reverse('sms:vhr_processed_panel', args=[self.report.id]),
            302,
        )]
        self.assertContains(response, success_message)

        next_response = self.client.get(
            reverse('sms:vhr_processed_panel', args=[self.report.id])
        )
        self.assertNotContains(next_response, success_message)

    def test_post_updates_existing_rer_instead_of_creating_a_second_one(self):
        rer = RiskEvaluationReportFactory(
            report=self.report,
            selected_risk=self.risk,
        )
        data = rer_form_data(self.report, self.risk)
        data['defenses'] = 'Defensas actualizadas.'

        response = self.client.post(self.url, data=data)

        assert response.status_code == 302
        assert RiskEvaluationReport.objects.filter(report=self.report).count() == 1
        rer.refresh_from_db()
        assert rer.defenses == 'Defensas actualizadas.'
        assert rer.analysis_status == 'PENDING'

    def test_resubmission_clears_stale_residual_values(self):
        RiskEvaluationReportFactory(
            report=self.report,
            selected_risk=self.risk,
            analysis_status='READY_FOR_REVIEW',
        )
        self.risk.post_evaluation_severity = 'D'
        self.risk.post_evaluation_probability = '2'
        self.risk.post_evaluation_justification = 'Justificación anterior.'
        self.risk.save(update_fields=[
            'post_evaluation_severity',
            'post_evaluation_probability',
            'post_evaluation_justification',
        ])

        response = self.client.post(
            self.url,
            data=rer_form_data(self.report, self.risk),
        )

        assert response.status_code == 302
        self.risk.refresh_from_db()
        assert self.risk.post_evaluation_severity == '0'
        assert self.risk.post_evaluation_probability == '0'
        assert self.risk.post_evaluation_justification == ''

    def test_form_displays_actions_for_every_report_risk(self):
        second_risk = RiskFactory(
            report=self.report,
            description='Segunda consecuencia considerada',
            pre_evaluation_severity='C',
            pre_evaluation_probability='2',
        )
        second_action = MitigationActionFactory(
            risk=second_risk,
            description='Segunda medida de mitigación',
            responsible=self.user,
        )
        MitigationActionEvidenceFactory(mitigation_action=second_action)

        response = self.client.get(self.url)

        assert response.status_code == 200
        self.assertContains(response, self.risk.description)
        self.assertContains(response, self.action.description)
        self.assertContains(response, second_risk.description)
        self.assertContains(response, second_action.description)

    def test_get_redirects_when_report_is_not_ready(self):
        self.action.evidence.delete()

        response = self.client.get(self.url)

        assert response.status_code == 302
        assert response.url == reverse(
            'sms:vhr_processed_panel',
            args=[self.report.id],
        )

    def test_user_without_sms_permission_cannot_request_rer_analysis(self):
        user_without_permission = StaffUserFactory(
            is_staff=True,
            is_superuser=False,
        )
        assert not user_without_permission.has_perm('accounts.can_manage_sms')
        self.client.force_login(user_without_permission)

        response = self.client.post(
            self.url,
            data=rer_form_data(self.report, self.risk),
        )

        assert response.status_code == 302
        assert response.url == reverse(
            'sms:vhr_processed_panel',
            args=[self.report.id],
        )
        assert not RiskEvaluationReport.objects.filter(report=self.report).exists()
