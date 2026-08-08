import json
from types import SimpleNamespace
from unittest.mock import Mock

from django.test import TestCase, override_settings

from sms.rer_ai import RERAIError, process_rer_analysis
from sms.test.factories import (
    MitigationActionEvidenceFactory,
    MitigationActionFactory,
    RiskEvaluationReportFactory,
    RiskFactory,
    StaffUserFactory,
    VoluntaryHazardReportFactory,
)


@override_settings(
    SARA_RER_ANALYSIS_MODEL='test-model',
    SARA_RER_ANALYSIS_PROMPT='Test RER prompt.',
    SARA_RER_ANALYSIS_MAX_OUTPUT_TOKENS=1000,
)
class TestRERAI(TestCase):
    def setUp(self):
        report = VoluntaryHazardReportFactory(
            code='SMS-RVP-500',
            description='Movimiento no autorizado en plataforma.',
            is_processed=True,
        )
        self.first_risk = self._create_complete_risk(
            report,
            'Colisión con una aeronave.',
            'B',
            '3',
        )
        self.second_risk = self._create_complete_risk(
            report,
            'Lesión del personal.',
            'C',
            '4',
        )
        self.rer = RiskEvaluationReportFactory(
            report=report,
            selected_risk=self.first_risk,
            analysis_status='PENDING',
        )

    def _create_complete_risk(self, report, description, severity, probability):
        risk = RiskFactory(
            report=report,
            description=description,
            pre_evaluation_severity=severity,
            pre_evaluation_probability=probability,
        )
        action = MitigationActionFactory(
            risk=risk,
            description='Aplicar una barrera operacional.',
            responsible=StaffUserFactory(),
        )
        MitigationActionEvidenceFactory(
            mitigation_action=action,
            description='Evidencia de la barrera aplicada.',
        )
        return risk

    def _client_with_results(self, results):
        client = Mock()
        client.responses.create.return_value = SimpleNamespace(
            status='completed',
            output=[],
            output_text=json.dumps({'risks': results}),
        )
        return client

    def _valid_results(self):
        return [
            {
                'risk_id': self.first_risk.pk,
                'residual_severity': 'B',
                'residual_probability': '2',
            },
            {
                'risk_id': self.second_risk.pk,
                'residual_severity': 'D',
                'residual_probability': '2',
            },
        ]

    def test_sara_updates_risk_residual_fields_directly(self):
        client = self._client_with_results(self._valid_results())

        process_rer_analysis(self.rer.pk, client=client)

        self.rer.refresh_from_db()
        self.first_risk.refresh_from_db()
        self.second_risk.refresh_from_db()
        assert self.rer.analysis_status == 'READY_FOR_REVIEW'
        assert self.rer.analysis_started_at is not None
        assert self.rer.analysis_completed_at is not None
        assert self.first_risk.post_evaluation_severity == 'B'
        assert self.first_risk.post_evaluation_probability == '2'
        assert self.second_risk.post_evaluation_severity == 'D'
        assert self.second_risk.post_evaluation_probability == '2'

        request = client.responses.create.call_args.kwargs
        payload = json.loads(request['input'])
        assert len(payload['risks']) == 2
        assert payload['risks'][0]['mitigation_actions'][0]['evidence']
        assert request['text']['format']['strict'] is True
        assert request['store'] is False

    def test_incomplete_results_fail_without_updating_any_risk(self):
        client = self._client_with_results(self._valid_results()[:1])

        with self.assertRaisesRegex(RERAIError, 'exactly one result'):
            process_rer_analysis(self.rer.pk, client=client)

        self.rer.refresh_from_db()
        self.first_risk.refresh_from_db()
        self.second_risk.refresh_from_db()
        assert self.rer.analysis_status == 'FAILED'
        assert self.first_risk.post_evaluation_severity == '0'
        assert self.second_risk.post_evaluation_severity == '0'

    def test_non_pending_rer_is_not_sent_to_sara(self):
        self.rer.analysis_status = 'READY_FOR_REVIEW'
        self.rer.save(update_fields=['analysis_status'])
        client = Mock()

        with self.assertRaisesRegex(RERAIError, 'not pending'):
            process_rer_analysis(self.rer.pk, client=client)

        client.responses.create.assert_not_called()
