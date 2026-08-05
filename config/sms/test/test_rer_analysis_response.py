from django.test import SimpleTestCase

from sms.services.rer_analysis_response import (
    RERAnalysisResponseError,
    ResidualRiskProposal,
    validate_rer_analysis_response,
)


def make_proposal(risk_id, **overrides):
    proposal = {
        'risk_id': risk_id,
        'residual_severity': 'D',
        'residual_probability': '2',
        'justification': 'Las medidas reducen la exposición operacional.',
    }
    proposal.update(overrides)
    return proposal


class TestRERAnalysisResponseValidation(SimpleTestCase):
    def test_accepts_one_valid_proposal_per_expected_risk(self):
        response = {'risks': [make_proposal(8), make_proposal(3)]}

        result = validate_rer_analysis_response(
            response,
            expected_risk_ids=[3, 8],
        )

        assert result.risks == (
            ResidualRiskProposal(
                risk_id=3,
                residual_severity='D',
                residual_probability='2',
                justification='Las medidas reducen la exposición operacional.',
            ),
            ResidualRiskProposal(
                risk_id=8,
                residual_severity='D',
                residual_probability='2',
                justification='Las medidas reducen la exposición operacional.',
            ),
        )

    def test_rejects_missing_and_unknown_risks(self):
        response = {'risks': [make_proposal(3), make_proposal(99)]}

        with self.assertRaisesRegex(
            RERAnalysisResponseError,
            'missing risk IDs: 8; unknown risk IDs: 99',
        ):
            validate_rer_analysis_response(response, expected_risk_ids=[3, 8])

    def test_rejects_duplicate_risks(self):
        response = {'risks': [make_proposal(3), make_proposal(3)]}

        with self.assertRaisesRegex(RERAnalysisResponseError, 'Duplicate risk IDs: 3'):
            validate_rer_analysis_response(response, expected_risk_ids=[3])

    def test_rejects_invalid_matrix_values(self):
        with self.assertRaisesRegex(RERAnalysisResponseError, 'invalid residual severity'):
            validate_rer_analysis_response(
                {'risks': [make_proposal(3, residual_severity='0')]},
                expected_risk_ids=[3],
            )

        with self.assertRaisesRegex(RERAnalysisResponseError, 'invalid residual probability'):
            validate_rer_analysis_response(
                {'risks': [make_proposal(3, residual_probability='6')]},
                expected_risk_ids=[3],
            )

        with self.assertRaisesRegex(RERAnalysisResponseError, 'invalid residual severity'):
            validate_rer_analysis_response(
                {'risks': [make_proposal(3, residual_severity=['D'])]},
                expected_risk_ids=[3],
            )

    def test_rejects_empty_justification(self):
        with self.assertRaisesRegex(RERAnalysisResponseError, 'non-empty justification'):
            validate_rer_analysis_response(
                {'risks': [make_proposal(3, justification='   ')]},
                expected_risk_ids=[3],
            )

    def test_rejects_unexpected_fields_at_every_level(self):
        with self.assertRaisesRegex(RERAnalysisResponseError, 'only the "risks" field'):
            validate_rer_analysis_response(
                {'risks': [make_proposal(3)], 'summary': 'extra'},
                expected_risk_ids=[3],
            )

        with self.assertRaisesRegex(RERAnalysisResponseError, 'invalid fields'):
            validate_rer_analysis_response(
                {'risks': [{**make_proposal(3), 'score': 'D2'}]},
                expected_risk_ids=[3],
            )
