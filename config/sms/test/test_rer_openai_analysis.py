import json
from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase, override_settings
from openai import APIError

from sms.services.rer_analysis_response import RERAnalysisResponseError
from sms.services.rer_openai_analysis import (
    RERAnalysisServiceError,
    request_rer_residual_analysis,
)


def make_payload():
    return {
        'rer': {'id': 10},
        'vhr': {'id': 20},
        'risks': [{'id': 2}, {'id': 5}],
    }


def make_response(output):
    return SimpleNamespace(
        status='completed',
        output=[],
        output_text=json.dumps(output, ensure_ascii=False),
    )


@override_settings(
    SARA_RER_ANALYSIS_MODEL='test-model',
    SARA_RER_ANALYSIS_PROMPT='Test residual-risk prompt.',
    SARA_RER_ANALYSIS_MAX_OUTPUT_TOKENS=1200,
)
class TestREROpenAIAnalysis(SimpleTestCase):
    def test_sends_strict_structured_request_and_returns_validated_result(self):
        client = Mock()
        client.responses.create.return_value = make_response({
            'risks': [
                {
                    'risk_id': 5,
                    'residual_severity': 'E',
                    'residual_probability': '1',
                    'justification': 'La exposición fue eliminada.',
                },
                {
                    'risk_id': 2,
                    'residual_severity': 'C',
                    'residual_probability': '2',
                    'justification': 'Las barreras reducen la probabilidad.',
                },
            ],
        })

        result = request_rer_residual_analysis(make_payload(), client=client)

        assert [proposal.risk_id for proposal in result.risks] == [2, 5]
        request = client.responses.create.call_args.kwargs
        assert request['model'] == 'test-model'
        assert request['instructions'] == 'Test residual-risk prompt.'
        assert json.loads(request['input']) == make_payload()
        assert request['text']['format']['type'] == 'json_schema'
        assert request['text']['format']['strict'] is True
        assert request['max_output_tokens'] == 1200
        assert request['store'] is False
        assert 'tools' not in request

    def test_rejects_incomplete_response(self):
        client = Mock()
        client.responses.create.return_value = SimpleNamespace(
            status='incomplete',
            incomplete_details=SimpleNamespace(reason='max_output_tokens'),
            output=[],
            output_text='',
        )

        with self.assertRaisesRegex(RERAnalysisServiceError, 'incomplete response'):
            request_rer_residual_analysis(make_payload(), client=client)

    def test_rejects_refusal(self):
        client = Mock()
        refusal = SimpleNamespace(type='refusal', refusal='Unable to comply.')
        message = SimpleNamespace(type='message', content=[refusal])
        client.responses.create.return_value = SimpleNamespace(
            status='completed',
            output=[message],
            output_text='',
        )

        with self.assertRaisesRegex(RERAnalysisServiceError, 'refused'):
            request_rer_residual_analysis(make_payload(), client=client)

    def test_rejects_invalid_json(self):
        client = Mock()
        client.responses.create.return_value = SimpleNamespace(
            status='completed',
            output=[],
            output_text='not-json',
        )

        with self.assertRaisesRegex(RERAnalysisServiceError, 'invalid JSON'):
            request_rer_residual_analysis(make_payload(), client=client)

    def test_preserves_domain_validation_at_the_service_boundary(self):
        client = Mock()
        client.responses.create.return_value = make_response({
            'risks': [
                {
                    'risk_id': 2,
                    'residual_severity': 'C',
                    'residual_probability': '2',
                    'justification': 'Mitigado.',
                },
            ],
        })

        with self.assertRaisesRegex(RERAnalysisResponseError, 'missing risk IDs: 5'):
            request_rer_residual_analysis(make_payload(), client=client)

    def test_wraps_openai_sdk_errors(self):
        client = Mock()
        client.responses.create.side_effect = APIError(
            'Service unavailable',
            request=Mock(),
            body=None,
        )

        with self.assertRaisesRegex(RERAnalysisServiceError, 'could not complete'):
            request_rer_residual_analysis(make_payload(), client=client)
