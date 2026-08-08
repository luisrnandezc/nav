"""SARA residual-risk analysis for Risk Evaluation Reports (RERs).

The management command calls ``process_rer_analysis``. This module intentionally
keeps the complete background workflow together so it is easy to follow.
"""

import json
import os

from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from openai import OpenAI, OpenAIError

from sms.models import MitigationAction, Risk, RiskEvaluationReport


VALID_SEVERITIES = {'A', 'B', 'C', 'D', 'E'}
VALID_PROBABILITIES = {'1', '2', '3', '4', '5'}

RESPONSE_SCHEMA = {
    'type': 'object',
    'properties': {
        'risks': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'risk_id': {'type': 'integer'},
                    'residual_severity': {
                        'type': 'string',
                        'enum': sorted(VALID_SEVERITIES),
                    },
                    'residual_probability': {
                        'type': 'string',
                        'enum': sorted(VALID_PROBABILITIES),
                    },
                },
                'required': [
                    'risk_id',
                    'residual_severity',
                    'residual_probability',
                ],
                'additionalProperties': False,
            },
        },
    },
    'required': ['risks'],
    'additionalProperties': False,
}


class RERAIError(RuntimeError):
    """Raised when SARA cannot produce a complete, valid RER analysis."""


def process_rer_analysis(rer_id, *, client=None):
    """Analyze one pending RER and save residual values directly on its risks."""
    rer, payload = _start_analysis(rer_id)

    try:
        raw_result = _request_sara_analysis(payload, client=client)
        results = _validate_results(raw_result, payload)
        _save_results(rer_id, results)
    except Exception as exc:
        _mark_failed(rer_id, exc)
        raise

    return results


@transaction.atomic
def _start_analysis(rer_id):
    rer = RiskEvaluationReport.objects.select_for_update().get(pk=rer_id)
    if rer.analysis_status != 'PENDING':
        raise RERAIError(f'RER {rer_id} is not pending analysis.')

    rer.analysis_status = 'PROCESSING'
    rer.analysis_error = ''
    rer.analysis_started_at = timezone.now()
    rer.analysis_completed_at = None
    rer.save(update_fields=[
        'analysis_status',
        'analysis_error',
        'analysis_started_at',
        'analysis_completed_at',
        'updated_at',
    ])
    return rer, _build_payload(rer)


def _build_payload(rer):
    """Represent the RER, all its risks, actions, and evidence as JSON-safe data."""
    actions = MitigationAction.objects.order_by('pk').select_related(
        'responsible',
        'evidence',
    )
    risks = rer.report.risks.order_by('pk').prefetch_related(
        Prefetch('mitigation_actions', queryset=actions, to_attr='rer_actions'),
    )

    return {
        'rer': {
            'id': rer.pk,
            'hazard': {
                'description': rer.hazard_description,
                'source': rer.get_hazard_source_display(),
                'type': rer.get_hazard_type_display(),
                'area': rer.get_hazard_area_display(),
                'possible_causes': rer.hazard_causes,
                'existing_defenses': rer.defenses,
            },
        },
        'vhr': {
            'id': rer.report_id,
            'code': rer.report.code,
            'description': rer.report.description,
        },
        'risks': [_serialize_risk(risk, rer.selected_risk_id) for risk in risks],
    }


def _serialize_risk(risk, priority_risk_id):
    return {
        'id': risk.pk,
        'description': risk.description,
        'is_priority': risk.pk == priority_risk_id,
        'initial_severity': risk.pre_evaluation_severity,
        'initial_probability': risk.pre_evaluation_probability,
        'mitigation_actions': [
            {
                'id': action.pk,
                'description': action.description,
                'responsible': (
                    action.responsible.get_full_name()
                    or action.responsible.get_username()
                ),
                'due_date': action.due_date.isoformat(),
                'follow_up_date': action.follow_date.isoformat(),
                'evidence': action.evidence.description,
            }
            for action in risk.rer_actions
        ],
    }


def _request_sara_analysis(payload, *, client=None):
    openai_client = client or _openai_client()
    try:
        response = openai_client.responses.create(
            model=settings.SARA_RER_ANALYSIS_MODEL,
            instructions=settings.SARA_RER_ANALYSIS_PROMPT,
            input=json.dumps(payload, ensure_ascii=False),
            reasoning={'effort': 'medium'},
            text={
                'format': {
                    'type': 'json_schema',
                    'name': 'rer_residual_risk_analysis',
                    'schema': RESPONSE_SCHEMA,
                    'strict': True,
                },
            },
            max_output_tokens=settings.SARA_RER_ANALYSIS_MAX_OUTPUT_TOKENS,
            store=False,
        )
    except OpenAIError as exc:
        raise RERAIError('OpenAI could not complete the RER analysis.') from exc

    if getattr(response, 'status', None) == 'incomplete':
        raise RERAIError('OpenAI returned an incomplete RER analysis.')

    for item in getattr(response, 'output', ()):
        for content in getattr(item, 'content', ()):
            if getattr(content, 'type', None) == 'refusal':
                raise RERAIError('OpenAI refused the RER analysis request.')

    try:
        return json.loads(response.output_text)
    except (AttributeError, TypeError, json.JSONDecodeError) as exc:
        raise RERAIError('OpenAI returned invalid JSON for the RER analysis.') from exc


def _openai_client():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise RERAIError('OPENAI_API_KEY is not configured.')
    return OpenAI(api_key=api_key)


def _validate_results(response, payload):
    """Apply the few domain checks required before updating Risk records."""
    if not isinstance(response, dict) or set(response) != {'risks'}:
        raise RERAIError('SARA returned an invalid response structure.')
    if not isinstance(response['risks'], list):
        raise RERAIError('SARA did not return a list of risks.')

    expected_ids = {risk['id'] for risk in payload['risks']}
    results = {}
    required_fields = {
        'risk_id',
        'residual_severity',
        'residual_probability',
    }

    for result in response['risks']:
        if not isinstance(result, dict) or set(result) != required_fields:
            raise RERAIError('SARA returned an invalid risk result.')
        risk_id = result['risk_id']
        if not isinstance(risk_id, int) or isinstance(risk_id, bool):
            raise RERAIError('SARA returned an invalid risk ID.')
        if risk_id in results:
            raise RERAIError(f'SARA returned risk {risk_id} more than once.')
        severity = result['residual_severity']
        probability = result['residual_probability']
        if not isinstance(severity, str) or severity not in VALID_SEVERITIES:
            raise RERAIError(f'SARA returned invalid severity for risk {risk_id}.')
        if (
            not isinstance(probability, str)
            or probability not in VALID_PROBABILITIES
        ):
            raise RERAIError(f'SARA returned invalid probability for risk {risk_id}.')
        results[risk_id] = result

    if set(results) != expected_ids:
        raise RERAIError('SARA did not return exactly one result for every RER risk.')
    return results


@transaction.atomic
def _save_results(rer_id, results):
    rer = RiskEvaluationReport.objects.select_for_update().get(pk=rer_id)
    if rer.analysis_status != 'PROCESSING':
        raise RERAIError(f'RER {rer_id} is no longer being processed.')

    risks = list(
        Risk.objects.select_for_update().filter(report_id=rer.report_id).order_by('pk')
    )
    if {risk.pk for risk in risks} != set(results):
        raise RERAIError('The RER risks changed before the results were saved.')

    for risk in risks:
        result = results[risk.pk]
        risk.post_evaluation_severity = result['residual_severity']
        risk.post_evaluation_probability = result['residual_probability']
    Risk.objects.bulk_update(
        risks,
        ['post_evaluation_severity', 'post_evaluation_probability'],
    )

    rer.analysis_status = 'READY_FOR_REVIEW'
    rer.analysis_error = ''
    rer.analysis_completed_at = timezone.now()
    rer.save(update_fields=[
        'analysis_status',
        'analysis_error',
        'analysis_completed_at',
        'updated_at',
    ])


@transaction.atomic
def _mark_failed(rer_id, exc):
    rer = RiskEvaluationReport.objects.select_for_update().get(pk=rer_id)
    if rer.analysis_status != 'PROCESSING':
        return
    rer.analysis_status = 'FAILED'
    if isinstance(exc, RERAIError):
        rer.analysis_error = str(exc)
    else:
        rer.analysis_error = 'Unexpected RER analysis error.'
    rer.analysis_completed_at = timezone.now()
    rer.save(update_fields=[
        'analysis_status',
        'analysis_error',
        'analysis_completed_at',
        'updated_at',
    ])
