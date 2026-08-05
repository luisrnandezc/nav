"""Response contract for SARA's residual-risk analysis."""

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable


VALID_RESIDUAL_SEVERITIES = frozenset({'A', 'B', 'C', 'D', 'E'})
VALID_RESIDUAL_PROBABILITIES = frozenset({'1', '2', '3', '4', '5'})

# This schema will be supplied to the OpenAI client in the next implementation
# step. The Python validator below remains the final boundary before persistence.
RER_ANALYSIS_RESPONSE_SCHEMA = {
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
                        'enum': sorted(VALID_RESIDUAL_SEVERITIES),
                    },
                    'residual_probability': {
                        'type': 'string',
                        'enum': sorted(VALID_RESIDUAL_PROBABILITIES),
                    },
                    'justification': {'type': 'string', 'minLength': 1},
                },
                'required': [
                    'risk_id',
                    'residual_severity',
                    'residual_probability',
                    'justification',
                ],
                'additionalProperties': False,
            },
        },
    },
    'required': ['risks'],
    'additionalProperties': False,
}


class RERAnalysisResponseError(ValueError):
    """Raised when SARA returns an incomplete or invalid RER analysis."""


@dataclass(frozen=True)
class ResidualRiskProposal:
    risk_id: int
    residual_severity: str
    residual_probability: str
    justification: str


@dataclass(frozen=True)
class RERAnalysisResult:
    risks: tuple[ResidualRiskProposal, ...]


def validate_rer_analysis_response(
    response: Any,
    *,
    expected_risk_ids: Iterable[int],
) -> RERAnalysisResult:
    """Validate and normalize SARA's decoded JSON response.

    An accepted response must contain exactly one proposal for every expected
    risk. This all-or-nothing rule prevents a partial analysis from being saved.
    """
    expected_ids = set(expected_risk_ids)
    if not isinstance(response, dict) or set(response) != {'risks'}:
        raise RERAnalysisResponseError(
            'The response must be an object containing only the "risks" field.'
        )

    raw_risks = response['risks']
    if not isinstance(raw_risks, list):
        raise RERAnalysisResponseError('The "risks" field must be a list.')

    proposals = tuple(
        _validate_proposal(raw_proposal, position=position)
        for position, raw_proposal in enumerate(raw_risks)
    )
    returned_ids = [proposal.risk_id for proposal in proposals]
    duplicate_ids = {
        risk_id for risk_id, count in Counter(returned_ids).items() if count > 1
    }
    if duplicate_ids:
        raise RERAnalysisResponseError(
            f'Duplicate risk IDs: {_format_ids(duplicate_ids)}.'
        )

    returned_id_set = set(returned_ids)
    missing_ids = expected_ids - returned_id_set
    unknown_ids = returned_id_set - expected_ids
    if missing_ids or unknown_ids:
        details = []
        if missing_ids:
            details.append(f'missing risk IDs: {_format_ids(missing_ids)}')
        if unknown_ids:
            details.append(f'unknown risk IDs: {_format_ids(unknown_ids)}')
        raise RERAnalysisResponseError('; '.join(details) + '.')

    # Stable ordering makes persistence and tests independent of model output order.
    return RERAnalysisResult(risks=tuple(sorted(proposals, key=lambda item: item.risk_id)))


def _validate_proposal(raw_proposal: Any, *, position: int) -> ResidualRiskProposal:
    required_fields = {
        'risk_id',
        'residual_severity',
        'residual_probability',
        'justification',
    }
    if not isinstance(raw_proposal, dict) or set(raw_proposal) != required_fields:
        raise RERAnalysisResponseError(
            f'Risk result at position {position} has invalid fields.'
        )

    risk_id = raw_proposal['risk_id']
    if not isinstance(risk_id, int) or isinstance(risk_id, bool):
        raise RERAnalysisResponseError(
            f'Risk result at position {position} has an invalid risk_id.'
        )

    severity = raw_proposal['residual_severity']
    if not isinstance(severity, str) or severity not in VALID_RESIDUAL_SEVERITIES:
        raise RERAnalysisResponseError(
            f'Risk {risk_id} has an invalid residual severity.'
        )

    probability = raw_proposal['residual_probability']
    if (
        not isinstance(probability, str)
        or probability not in VALID_RESIDUAL_PROBABILITIES
    ):
        raise RERAnalysisResponseError(
            f'Risk {risk_id} has an invalid residual probability.'
        )

    justification = raw_proposal['justification']
    if not isinstance(justification, str) or not justification.strip():
        raise RERAnalysisResponseError(
            f'Risk {risk_id} requires a non-empty justification.'
        )

    return ResidualRiskProposal(
        risk_id=risk_id,
        residual_severity=severity,
        residual_probability=probability,
        justification=justification.strip(),
    )


def _format_ids(risk_ids: Iterable[int]) -> str:
    return ', '.join(str(risk_id) for risk_id in sorted(risk_ids))
