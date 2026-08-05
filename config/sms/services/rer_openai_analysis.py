"""OpenAI adapter for RER residual-risk analysis."""

import json
import os
from typing import Any

from django.conf import settings
from openai import OpenAI, OpenAIError

from sms.models import RiskEvaluationReport
from sms.services.rer_analysis import build_rer_analysis_payload
from sms.services.rer_analysis_response import (
    RER_ANALYSIS_RESPONSE_SCHEMA,
    RERAnalysisResult,
    validate_rer_analysis_response,
)


class RERAnalysisServiceError(RuntimeError):
    """Raised when the external analysis could not produce a usable response."""


def analyze_rer_residual_risks(
    rer: RiskEvaluationReport,
    *,
    client: Any = None,
) -> RERAnalysisResult:
    """Request and validate SARA's residual analysis without writing to the DB."""
    payload = build_rer_analysis_payload(rer)
    return request_rer_residual_analysis(payload, client=client)


def request_rer_residual_analysis(
    payload: dict[str, Any],
    *,
    client: Any = None,
) -> RERAnalysisResult:
    """Send a prepared RER payload to OpenAI and return a validated result."""
    openai_client = client or _build_openai_client()

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
                    'schema': RER_ANALYSIS_RESPONSE_SCHEMA,
                    'strict': True,
                },
            },
            max_output_tokens=settings.SARA_RER_ANALYSIS_MAX_OUTPUT_TOKENS,
            store=False,
        )
    except OpenAIError as exc:
        raise RERAnalysisServiceError(
            'OpenAI could not complete the RER residual-risk analysis.'
        ) from exc

    output_text = _extract_output_text(response)
    try:
        decoded_response = json.loads(output_text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise RERAnalysisServiceError(
            'OpenAI returned an invalid JSON response for the RER analysis.'
        ) from exc

    expected_risk_ids = [risk['id'] for risk in payload['risks']]
    return validate_rer_analysis_response(
        decoded_response,
        expected_risk_ids=expected_risk_ids,
    )


def _build_openai_client() -> OpenAI:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise RERAnalysisServiceError(
            'The OPENAI_API_KEY environment variable is not configured.'
        )
    return OpenAI(api_key=api_key)


def _extract_output_text(response: Any) -> str:
    if getattr(response, 'status', None) == 'incomplete':
        reason = getattr(getattr(response, 'incomplete_details', None), 'reason', None)
        detail = f' Reason: {reason}.' if reason else ''
        raise RERAnalysisServiceError(f'OpenAI returned an incomplete response.{detail}')

    # Refusals are represented as content items rather than regular output text.
    for output_item in getattr(response, 'output', ()):
        if getattr(output_item, 'type', None) != 'message':
            continue
        for content_item in getattr(output_item, 'content', ()):
            if getattr(content_item, 'type', None) == 'refusal':
                raise RERAnalysisServiceError(
                    'OpenAI refused to perform the RER residual-risk analysis.'
                )

    output_text = getattr(response, 'output_text', None)
    if not isinstance(output_text, str) or not output_text.strip():
        raise RERAnalysisServiceError(
            'OpenAI returned no content for the RER residual-risk analysis.'
        )
    return output_text
