from django.test import TestCase

from sms.rer_readiness import evaluate_rer_readiness
from sms.test.factories import (
    MitigationActionEvidenceFactory,
    MitigationActionFactory,
    RiskFactory,
    StaffUserFactory,
    VoluntaryHazardReportFactory,
)


class TestRERReadiness(TestCase):
    def make_complete_report(self):
        report = VoluntaryHazardReportFactory(
            code='SMS-RVP-200',
            is_processed=True,
        )
        risk = RiskFactory(
            report=report,
            pre_evaluation_severity='B',
            pre_evaluation_probability='3',
        )
        action = MitigationActionFactory(
            risk=risk,
            responsible=StaffUserFactory(),
        )
        MitigationActionEvidenceFactory(mitigation_action=action)
        return report

    def test_complete_processed_report_is_ready(self):
        result = evaluate_rer_readiness(self.make_complete_report())

        assert result.is_ready
        assert result.errors == ()

    def test_report_requires_processed_state_and_code(self):
        report = self.make_complete_report()
        report.is_processed = False
        report.code = None

        result = evaluate_rer_readiness(report)

        assert not result.is_ready
        assert any('procesado' in error for error in result.errors)
        assert any('código único' in error for error in result.errors)

    def test_every_risk_requires_initial_evaluation_and_an_action(self):
        report = self.make_complete_report()
        RiskFactory(
            report=report,
            pre_evaluation_severity='0',
            pre_evaluation_probability='0',
        )

        result = evaluate_rer_readiness(report)

        assert not result.is_ready
        assert any('severidad inicial' in error for error in result.errors)
        assert any('probabilidad inicial' in error for error in result.errors)
        assert any('al menos una MMR' in error for error in result.errors)

    def test_every_action_requires_responsible_and_evidence(self):
        report = self.make_complete_report()
        risk = report.risks.first()
        MitigationActionFactory(
            risk=risk,
            responsible=None,
        )

        result = evaluate_rer_readiness(report)

        assert not result.is_ready
        assert any('responsable asignado' in error for error in result.errors)
        assert any('evidencia registrada' in error for error in result.errors)
