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
        'post_evaluation_severity': 'D',
        'post_evaluation_probability': '2',
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

    def test_existing_rer_populates_residual_evaluation(self):
        rer = RiskEvaluationReportFactory()
        rer.selected_risk.post_evaluation_severity = 'C'
        rer.selected_risk.post_evaluation_probability = '3'
        rer.selected_risk.save()

        form = RiskEvaluationReportForm(report=rer.report, instance=rer)

        assert form['post_evaluation_severity'].value() == 'C'
        assert form['post_evaluation_probability'].value() == '3'


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

    def test_post_creates_rer_and_updates_selected_risk_residual_values(self):
        response = self.client.post(
            self.url,
            data=rer_form_data(self.report, self.risk),
        )

        assert response.status_code == 302
        rer = RiskEvaluationReport.objects.get(report=self.report)
        assert rer.selected_risk_id == self.risk.id

        self.risk.refresh_from_db()
        assert self.risk.post_evaluation_severity == 'D'
        assert self.risk.post_evaluation_probability == '2'

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

    def test_get_redirects_when_report_is_not_ready(self):
        self.action.evidence.delete()

        response = self.client.get(self.url)

        assert response.status_code == 302
        assert response.url == reverse(
            'sms:vhr_processed_panel',
            args=[self.report.id],
        )
