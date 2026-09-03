from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from sms.models import RiskEvaluationReport
from sms.test.factories import (
    MitigationActionEvidenceFactory,
    MitigationActionFactory,
    RiskFactory,
    StaffUserFactory,
    VoluntaryHazardReportFactory,
)


class TestRERJourney(TestCase):
    """Exercise the complete RER workflow, with only the OpenAI call mocked."""

    def setUp(self):
        self.coordinator = StaffUserFactory(is_staff=True, is_superuser=True)
        self.client.force_login(self.coordinator)
        self.report = VoluntaryHazardReportFactory(
            code='SMS-RVP-JOURNEY-001',
            is_processed=True,
            area='OPERATIONS',
            description='Ingreso no coordinado de un vehículo a la plataforma.',
        )
        self.priority_risk = self._create_complete_risk(
            description='Colisión del vehículo con una aeronave.',
            severity='B',
            probability='4',
            action='Restringir el acceso mediante control de autorización.',
        )
        self.second_risk = self._create_complete_risk(
            description='Lesión del personal presente en plataforma.',
            severity='C',
            probability='3',
            action='Delimitar y señalizar el área de circulación.',
        )

    def _create_complete_risk(self, *, description, severity, probability, action):
        risk = RiskFactory(
            report=self.report,
            description=description,
            pre_evaluation_severity=severity,
            pre_evaluation_probability=probability,
        )
        mitigation = MitigationActionFactory(
            risk=risk,
            description=action,
            responsible=self.coordinator,
        )
        MitigationActionEvidenceFactory(
            mitigation_action=mitigation,
            description=f'Evidencia para: {action}',
        )
        return risk

    def _rer_form_data(self):
        return {
            'registration_date': timezone.localdate().isoformat(),
            'sms_user_fullname': 'Coordinador SMS',
            'dir_user_fullname': 'Director General',
            'hazard_description': self.report.description,
            'hazard_source': 'VHR',
            'hazard_type': 'ORG',
            'hazard_area': self.report.area,
            'selected_risk': self.priority_risk.pk,
            'hazard_causes': 'Acceso sin coordinación ni autorización previa.',
            'defenses': 'Procedimiento de circulación en plataforma.',
        }

    def _sara_results(self):
        return {
            'risks': [
                {
                    'risk_id': self.priority_risk.pk,
                    'residual_severity': 'B',
                    'residual_probability': '2',
                    'justification': 'El control reduce la probabilidad de acceso.',
                },
                {
                    'risk_id': self.second_risk.pk,
                    'residual_severity': 'C',
                    'residual_probability': '1',
                    'justification': 'La delimitación reduce la exposición del personal.',
                },
            ],
        }

    def _review_form_data(self):
        return {
            # Django formsets require these management fields. TOTAL_FORMS and
            # INITIAL_FORMS describe the two submitted risk forms. MIN_NUM_FORMS
            # and MAX_NUM_FORMS mirror the bounds rendered by Django; they are
            # formset metadata rather than residual-risk values.
            'risks-TOTAL_FORMS': '2',
            'risks-INITIAL_FORMS': '2',
            'risks-MIN_NUM_FORMS': '0',
            'risks-MAX_NUM_FORMS': '1000',
            'risks-0-id': str(self.priority_risk.pk),
            'risks-0-post_evaluation_severity': 'B',
            # The coordinator overrides SARA's probability from 2 to 1.
            'risks-0-post_evaluation_probability': '1',
            'risks-0-post_evaluation_justification': (
                'El coordinador considera suficientes los controles implementados.'
            ),
            'risks-1-id': str(self.second_risk.pk),
            'risks-1-post_evaluation_severity': 'C',
            'risks-1-post_evaluation_probability': '1',
            'risks-1-post_evaluation_justification': (
                'La delimitación reduce la exposición del personal.'
            ),
        }

    @patch('sms.rer_ai._request_sara_analysis')
    def test_complete_rer_workflow(self, request_sara_analysis):
        # The coordinator prepares the RER and queues it for SARA.
        response = self.client.post(
            reverse('sms:rer_form', args=[self.report.pk]),
            self._rer_form_data(),
        )

        assert response.status_code == 302
        rer = RiskEvaluationReport.objects.get(report=self.report)
        assert rer.analysis_status == 'PENDING'
        assert rer.selected_risk == self.priority_risk

        dashboard = self.client.get(reverse('sms:rer_dashboard'))
        assert self.report in dashboard.context['pending_rer_reports']

        # The real command runs the real processor; only the external API is mocked.
        request_sara_analysis.return_value = self._sara_results()
        call_command('process_pending_rer_analyses', stdout=StringIO())

        rer.refresh_from_db()
        self.priority_risk.refresh_from_db()
        self.second_risk.refresh_from_db()
        assert rer.analysis_status == 'READY_FOR_REVIEW'
        assert self.priority_risk.post_evaluation() == 'B2'
        assert self.second_risk.post_evaluation() == 'C1'

        dashboard = self.client.get(reverse('sms:rer_dashboard'))
        assert self.report in dashboard.context['pending_review_reports']
        assert self.report not in dashboard.context['pending_rer_reports']

        # The coordinator sees SARA's result and approves a manual override.
        action_panel_url = reverse('sms:rer_action_panel', args=[rer.pk])
        action_panel = self.client.get(action_panel_url)
        assert action_panel.status_code == 200
        self.assertContains(action_panel, self.priority_risk.description)
        self.assertContains(action_panel, 'El control reduce la probabilidad de acceso.')

        response = self.client.post(action_panel_url, self._review_form_data())

        assert response.status_code == 302
        assert response.url == reverse('sms:rer_dashboard')
        rer.refresh_from_db()
        self.priority_risk.refresh_from_db()
        self.second_risk.refresh_from_db()
        assert rer.analysis_status == 'REVIEWED'
        assert rer.reviewed_by == self.coordinator
        assert rer.reviewed_at is not None
        assert self.priority_risk.post_evaluation() == 'B1'
        assert self.priority_risk.post_evaluation_justification.startswith(
            'El coordinador considera'
        )
        assert self.second_risk.post_evaluation() == 'C1'

        dashboard = self.client.get(reverse('sms:rer_dashboard'))
        assert self.report in dashboard.context['completed_rer_reports']
        assert self.report not in dashboard.context['pending_review_reports']
