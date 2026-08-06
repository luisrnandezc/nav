"""Coordinate the lifecycle of one pending RER residual-risk analysis."""

from collections.abc import Callable

from django.db import transaction
from django.utils import timezone

from sms.models import RiskEvaluationReport, RiskResidualEvaluation
from sms.services.rer_analysis import build_rer_analysis_payload
from sms.services.rer_analysis_response import (
    RERAnalysisResponseError,
    RERAnalysisResult,
    validate_rer_analysis_response,
)
from sms.services.rer_openai_analysis import (
    RERAnalysisServiceError,
    request_rer_residual_analysis,
)


class RERAnalysisStateError(RuntimeError):
    """Raised when an RER cannot transition from its current analysis state."""


class RERAnalysisInputChangedError(RuntimeError):
    """Raised when report data changes while SARA is analyzing its snapshot."""


AnalysisService = Callable[[dict], RERAnalysisResult]


def process_pending_rer_analysis(
    rer_id: int,
    *,
    analysis_service: AnalysisService = request_rer_residual_analysis,
) -> RERAnalysisResult:
    """Analyze one pending RER and persist all proposals atomically.

    The external request runs without an open database transaction. This avoids
    holding locks during a potentially slow network operation.
    """
    payload = _claim_pending_rer(rer_id)

    try:
        result = analysis_service(payload)
        _persist_analysis_result(rer_id, payload=payload, result=result)
    except Exception as exc:
        _mark_analysis_failed(rer_id, exc)
        raise

    return result


@transaction.atomic
def _claim_pending_rer(rer_id: int) -> dict:
    # Row locking makes the PENDING -> PROCESSING transition exclusive. A second
    # worker will see PROCESSING after this short transaction is committed.
    rer = RiskEvaluationReport.objects.select_for_update().get(pk=rer_id)
    if rer.analysis_status != 'PENDING':
        raise RERAnalysisStateError(
            f'RER {rer_id} is {rer.analysis_status}, not PENDING.'
        )

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

    # PENDING means any earlier proposal is obsolete, including data left by a
    # manually retried or interrupted process.
    rer.residual_evaluations.all().delete()
    return build_rer_analysis_payload(rer)


@transaction.atomic
def _persist_analysis_result(
    rer_id: int,
    *,
    payload: dict,
    result: RERAnalysisResult,
) -> None:
    rer = RiskEvaluationReport.objects.select_for_update().get(pk=rer_id)
    if rer.analysis_status != 'PROCESSING':
        raise RERAnalysisStateError(
            f'RER {rer_id} is no longer being processed.'
        )

    # Rebuild the complete input to prevent saving an answer generated from data
    # that a user edited while the external analysis was running.
    current_payload = build_rer_analysis_payload(rer)
    if current_payload != payload:
        raise RERAnalysisInputChangedError(
            'The RER data changed while SARA was analyzing it.'
        )

    validated_result = _revalidate_result(result, payload=payload)
    RiskResidualEvaluation.objects.bulk_create([
        RiskResidualEvaluation(
            rer=rer,
            risk_id=proposal.risk_id,
            proposed_severity=proposal.residual_severity,
            proposed_probability=proposal.residual_probability,
            justification=proposal.justification,
        )
        for proposal in validated_result.risks
    ])

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
def _mark_analysis_failed(rer_id: int, exc: Exception) -> None:
    rer = RiskEvaluationReport.objects.select_for_update().get(pk=rer_id)

    # A user may have resubmitted the RER while an old request was finishing. In
    # that case, preserve the newer PENDING state instead of overwriting it.
    if rer.analysis_status != 'PROCESSING':
        return

    rer.residual_evaluations.all().delete()
    rer.analysis_status = 'FAILED'
    rer.analysis_error = _safe_error_message(exc)
    rer.analysis_completed_at = timezone.now()
    rer.save(update_fields=[
        'analysis_status',
        'analysis_error',
        'analysis_completed_at',
        'updated_at',
    ])


def _safe_error_message(exc: Exception) -> str:
    safe_errors = (
        RERAnalysisServiceError,
        RERAnalysisResponseError,
        RERAnalysisInputChangedError,
        RERAnalysisStateError,
    )
    if isinstance(exc, safe_errors):
        return str(exc)
    return 'Unexpected error while processing the RER residual-risk analysis.'


def _revalidate_result(
    result: RERAnalysisResult,
    *,
    payload: dict,
) -> RERAnalysisResult:
    """Protect persistence even if a future analysis adapter skips validation."""
    response = {
        'risks': [
            {
                'risk_id': proposal.risk_id,
                'residual_severity': proposal.residual_severity,
                'residual_probability': proposal.residual_probability,
                'justification': proposal.justification,
            }
            for proposal in result.risks
        ]
    }
    return validate_rer_analysis_response(
        response,
        expected_risk_ids=[risk['id'] for risk in payload['risks']],
    )
