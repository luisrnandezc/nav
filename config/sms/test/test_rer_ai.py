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
        return self._client_with_response({'risks': results})

    def _client_with_response(self, response):
        client = Mock()
        client.responses.create.return_value = SimpleNamespace(
            status='completed',
            output=[],
            output_text=json.dumps(response),
        )
        return client

    def _assert_response_fails_without_updates(self, response, error):
        client = self._client_with_response(response)

        with self.assertRaisesRegex(RERAIError, error):
            process_rer_analysis(self.rer.pk, client=client)

        self.rer.refresh_from_db()
        self.first_risk.refresh_from_db()
        self.second_risk.refresh_from_db()
        assert self.rer.analysis_status == 'FAILED'
        assert self.rer.analysis_error
        assert self.first_risk.post_evaluation_severity == '0'
        assert self.first_risk.post_evaluation_probability == '0'
        assert self.second_risk.post_evaluation_severity == '0'
        assert self.second_risk.post_evaluation_probability == '0'

    def _valid_results(self):
        return [
            {
                'risk_id': self.first_risk.pk,
                'residual_severity': 'B',
                'residual_probability': '2',
                'justification': 'La barrera reduce la probabilidad de exposición.',
            },
            {
                'risk_id': self.second_risk.pk,
                'residual_severity': 'D',
                'residual_probability': '2',
                'justification': 'La medida limita el posible daño al personal.',
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
        assert 'reduce la probabilidad' in (
            self.first_risk.post_evaluation_justification
        )
        assert self.second_risk.post_evaluation_severity == 'D'
        assert self.second_risk.post_evaluation_probability == '2'

        request = client.responses.create.call_args.kwargs
        payload = json.loads(request['input'])
        assert len(payload['risks']) == 2
        assert payload['risks'][0]['mitigation_actions'][0]['evidence']
        assert request['text']['format']['strict'] is True
        assert request['store'] is False

    def test_incomplete_results_fail_without_updating_any_risk(self):
        self._assert_response_fails_without_updates(
            {'risks': self._valid_results()[:1]},
            'exactly one result',
        )

    def test_unknown_risk_id_is_rejected(self):
        results = self._valid_results()
        results[0]['risk_id'] = 999999

        self._assert_response_fails_without_updates(
            {'risks': results},
            'exactly one result',
        )

    def test_duplicate_risk_id_is_rejected(self):
        results = self._valid_results()
        results[1]['risk_id'] = self.first_risk.pk

        self._assert_response_fails_without_updates(
            {'risks': results},
            'more than once',
        )

    def test_invalid_severity_is_rejected(self):
        results = self._valid_results()
        results[0]['residual_severity'] = 'F'

        self._assert_response_fails_without_updates(
            {'risks': results},
            'invalid severity',
        )

    def test_invalid_probability_is_rejected(self):
        results = self._valid_results()
        results[0]['residual_probability'] = '6'

        self._assert_response_fails_without_updates(
            {'risks': results},
            'invalid probability',
        )

    def test_empty_justification_is_rejected(self):
        results = self._valid_results()
        results[0]['justification'] = '   '

        self._assert_response_fails_without_updates(
            {'risks': results},
            'omitted the justification',
        )

    def test_malformed_response_structure_is_rejected(self):
        self._assert_response_fails_without_updates(
            {'unexpected': self._valid_results()},
            'invalid response structure',
        )

    def test_non_pending_rer_is_not_sent_to_sara(self):
        self.rer.analysis_status = 'READY_FOR_REVIEW'
        self.rer.save(update_fields=['analysis_status'])
        client = Mock()

        with self.assertRaisesRegex(RERAIError, 'not pending'):
            process_rer_analysis(self.rer.pk, client=client)

        client.responses.create.assert_not_called()
