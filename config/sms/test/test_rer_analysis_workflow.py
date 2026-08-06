from datetime import date

from django.test import TestCase

from sms.models import RiskResidualEvaluation
from sms.services.rer_analysis_response import (
    RERAnalysisResponseError,
    RERAnalysisResult,
    ResidualRiskProposal,
)
from sms.services.rer_analysis_workflow import (
    RERAnalysisInputChangedError,
    RERAnalysisStateError,
    process_pending_rer_analysis,
)
from sms.services.rer_openai_analysis import RERAnalysisServiceError
from sms.test.factories import (
    MitigationActionEvidenceFactory,
    MitigationActionFactory,
    RiskEvaluationReportFactory,
    RiskFactory,
    StaffUserFactory,
    VoluntaryHazardReportFactory,
)


class TestRERAnalysisWorkflow(TestCase):
    def setUp(self):
        report = VoluntaryHazardReportFactory(
            code='SMS-RVP-400',
            is_processed=True,
        )
        self.first_risk = self._add_complete_risk(
            report,
            description='Colisión con una aeronave estacionada.',
            severity='B',
            probability='3',
        )
        self.second_risk = self._add_complete_risk(
            report,
            description='Lesión del personal de plataforma.',
            severity='C',
            probability='4',
        )
        self.rer = RiskEvaluationReportFactory(
            report=report,
            selected_risk=self.first_risk,
            registration_date=date(2026, 8, 6),
            analysis_status='PENDING',
        )

    def _add_complete_risk(
        self,
        report,
        *,
        description,
        severity,
        probability,
    ):
        risk = RiskFactory(
            report=report,
            description=description,
            pre_evaluation_severity=severity,
            pre_evaluation_probability=probability,
        )
        action = MitigationActionFactory(
            risk=risk,
            responsible=StaffUserFactory(),
        )
        MitigationActionEvidenceFactory(mitigation_action=action)
        return risk

    def make_result(self):
        return RERAnalysisResult(risks=(
            ResidualRiskProposal(
                risk_id=self.first_risk.pk,
                residual_severity='B',
                residual_probability='2',
                justification='La medida reduce la exposición.',
            ),
            ResidualRiskProposal(
                risk_id=self.second_risk.pk,
                residual_severity='D',
                residual_probability='2',
                justification='La barrera limita la exposición del personal.',
            ),
        ))

    def test_success_persists_every_proposal_and_marks_ready(self):
        captured_statuses = []

        def analysis_service(payload):
            self.rer.refresh_from_db()
            captured_statuses.append(self.rer.analysis_status)
            assert {risk['id'] for risk in payload['risks']} == {
                self.first_risk.pk,
                self.second_risk.pk,
            }
            return self.make_result()

        result = process_pending_rer_analysis(
            self.rer.pk,
            analysis_service=analysis_service,
        )

        self.rer.refresh_from_db()
        assert result == self.make_result()
        assert captured_statuses == ['PROCESSING']
        assert self.rer.analysis_status == 'READY_FOR_REVIEW'
        assert self.rer.analysis_started_at is not None
        assert self.rer.analysis_completed_at is not None
        assert self.rer.analysis_error == ''
        assert self.rer.residual_evaluations.count() == 2
        assert self.first_risk.residual_evaluation.proposed_probability == '2'
        self.first_risk.refresh_from_db()
        assert self.first_risk.post_evaluation_severity == '0'
        assert self.first_risk.post_evaluation_probability == '0'

    def test_only_pending_rer_can_be_claimed(self):
        self.rer.analysis_status = 'PROCESSING'
        self.rer.save(update_fields=['analysis_status'])
        analysis_called = False

        def analysis_service(payload):
            nonlocal analysis_called
            analysis_called = True
            return self.make_result()

        with self.assertRaisesRegex(RERAnalysisStateError, 'not PENDING'):
            process_pending_rer_analysis(
                self.rer.pk,
                analysis_service=analysis_service,
            )

        assert analysis_called is False
        assert not RiskResidualEvaluation.objects.exists()

    def test_service_failure_marks_rer_failed_without_partial_results(self):
        def analysis_service(payload):
            raise RERAnalysisServiceError('SARA is temporarily unavailable.')

        with self.assertRaisesRegex(RERAnalysisServiceError, 'temporarily unavailable'):
            process_pending_rer_analysis(
                self.rer.pk,
                analysis_service=analysis_service,
            )

        self.rer.refresh_from_db()
        assert self.rer.analysis_status == 'FAILED'
        assert self.rer.analysis_error == 'SARA is temporarily unavailable.'
        assert self.rer.analysis_completed_at is not None
        assert not self.rer.residual_evaluations.exists()

    def test_input_change_during_analysis_rejects_stale_result(self):
        action = self.first_risk.mitigation_actions.get()

        def analysis_service(payload):
            action.description = 'Medida modificada mientras SARA analizaba.'
            action.save(update_fields=['description'])
            return self.make_result()

        with self.assertRaisesRegex(RERAnalysisInputChangedError, 'data changed'):
            process_pending_rer_analysis(
                self.rer.pk,
                analysis_service=analysis_service,
            )

        self.rer.refresh_from_db()
        assert self.rer.analysis_status == 'FAILED'
        assert 'data changed' in self.rer.analysis_error
        assert not self.rer.residual_evaluations.exists()

    def test_incomplete_result_is_rejected_before_persistence(self):
        incomplete_result = RERAnalysisResult(risks=(
            self.make_result().risks[0],
        ))

        with self.assertRaisesRegex(RERAnalysisResponseError, 'missing risk IDs'):
            process_pending_rer_analysis(
                self.rer.pk,
                analysis_service=lambda payload: incomplete_result,
            )

        self.rer.refresh_from_db()
        assert self.rer.analysis_status == 'FAILED'
        assert 'missing risk IDs' in self.rer.analysis_error
        assert not self.rer.residual_evaluations.exists()

    def test_second_processing_attempt_is_rejected(self):
        process_pending_rer_analysis(
            self.rer.pk,
            analysis_service=lambda payload: self.make_result(),
        )

        with self.assertRaisesRegex(RERAnalysisStateError, 'not PENDING'):
            process_pending_rer_analysis(
                self.rer.pk,
                analysis_service=lambda payload: self.make_result(),
            )

        assert self.rer.residual_evaluations.count() == 2
