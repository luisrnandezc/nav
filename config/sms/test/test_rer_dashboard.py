from django.test import TestCase
from django.urls import reverse

from sms.test.factories import (
    MitigationActionFactory,
    RiskEvaluationReportFactory,
    RiskFactory,
    StaffUserFactory,
    VoluntaryHazardReportFactory,
)


class TestRERDashboard(TestCase):
    def setUp(self):
        self.user = StaffUserFactory()
        self.client.force_login(self.user)
        self.url = reverse('sms:rer_dashboard')

    def test_only_processed_reports_are_listed(self):
        processed = VoluntaryHazardReportFactory(
            code='SMS-RVP-PROCESSED',
            is_processed=True,
        )
        unprocessed = VoluntaryHazardReportFactory(
            code='SMS-RVP-UNPROCESSED',
            is_processed=False,
        )

        response = self.client.get(self.url)

        assert response.status_code == 200
        self.assertContains(response, processed.code)
        self.assertNotContains(response, unprocessed.code)

    def test_processed_report_without_rer_is_pending(self):
        report = VoluntaryHazardReportFactory(is_processed=True)

        response = self.client.get(self.url)

        assert report in response.context['pending_rer_reports']
        assert report not in response.context['completed_rer_reports']

    def test_pre_review_rer_statuses_are_pending_analysis(self):
        statuses = [
            'DRAFT',
            'PENDING',
            'PROCESSING',
            'FAILED',
        ]
        reports = []
        for index, status in enumerate(statuses):
            report = VoluntaryHazardReportFactory(
                code=f'SMS-RVP-PENDING-{index}',
                is_processed=True,
            )
            RiskEvaluationReportFactory(
                report=report,
                analysis_status=status,
            )
            reports.append(report)

        response = self.client.get(self.url)
        pending_ids = {
            report.id for report in response.context['pending_rer_reports']
        }

        assert pending_ids == {report.id for report in reports}

    def test_ready_rer_is_pending_human_review(self):
        report = VoluntaryHazardReportFactory(is_processed=True)
        rer = RiskEvaluationReportFactory(
            report=report,
            analysis_status='READY_FOR_REVIEW',
        )

        response = self.client.get(self.url)

        assert report in response.context['pending_review_reports']
        assert report not in response.context['pending_rer_reports']
        self.assertContains(response, reverse('sms:rer_action_panel', args=[rer.id]))

    def test_reviewed_rer_is_completed(self):
        report = VoluntaryHazardReportFactory(
            code='SMS-RVP-COMPLETED',
            is_processed=True,
        )
        rer = RiskEvaluationReportFactory(
            report=report,
            analysis_status='REVIEWED',
        )

        response = self.client.get(self.url)

        assert report in response.context['completed_rer_reports']
        assert report not in response.context['pending_rer_reports']
        assert report not in response.context['pending_review_reports']
        self.assertContains(response, reverse('sms:rer_action_panel', args=[rer.id]))

    def test_card_contains_risk_and_mitigation_action_counts(self):
        report = VoluntaryHazardReportFactory(is_processed=True)
        first_risk = RiskFactory(report=report)
        second_risk = RiskFactory(report=report)
        MitigationActionFactory(risk=first_risk)
        MitigationActionFactory(risk=first_risk)
        MitigationActionFactory(risk=second_risk)

        response = self.client.get(self.url)
        listed_report = response.context['pending_rer_reports'].get(id=report.id)

        assert listed_report.risk_count == 2
        assert listed_report.mitigation_action_count == 3

    def test_sms_dashboard_rer_button_uses_dashboard_route(self):
        response = self.client.get(reverse('sms:sms_dashboard'))

        self.assertContains(response, f'href="{self.url}"')

    def test_processed_report_panel_returns_to_rer_dashboard(self):
        report = VoluntaryHazardReportFactory(is_processed=True)

        response = self.client.get(
            reverse('sms:vhr_processed_panel', args=[report.id]),
            HTTP_REFERER=f'http://testserver{self.url}',
        )

        assert response.status_code == 200
        assert response.context['back_url'] == self.url
