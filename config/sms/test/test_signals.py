"""
SMS app – report resolved status when all risks are mitigated.
"""
from django.test import TestCase

from sms.models import VoluntaryHazardReport, Risk, MitigationAction
from sms.signals import check_and_update_report_resolved_status
from sms.test.factories import (
    VoluntaryHazardReportFactory,
    RiskFactory,
    MitigationActionFactory,
)


class TestReportResolvedStatus(TestCase):
    """VHR is_resolved updates when all risks are MITIGATED."""

    def test_report_stays_unresolved_when_any_risk_unmitigated(self):
        report = VoluntaryHazardReportFactory(is_resolved=False)
        RiskFactory(report=report, condition="MITIGATED")
        RiskFactory(report=report, condition="UNMITIGATED")
        check_and_update_report_resolved_status(report)
        report.refresh_from_db()
        assert report.is_resolved is False

    def test_report_becomes_resolved_when_all_risks_mitigated(self):
        report = VoluntaryHazardReportFactory(is_resolved=False)
        RiskFactory(report=report, condition="MITIGATED")
        RiskFactory(report=report, condition="MITIGATED")
        check_and_update_report_resolved_status(report)
        report.refresh_from_db()
        assert report.is_resolved is True

    def test_report_with_no_risks_stays_unresolved(self):
        report = VoluntaryHazardReportFactory(is_resolved=True)
        check_and_update_report_resolved_status(report)
        report.refresh_from_db()
        assert report.is_resolved is False

    def test_saving_risk_with_condition_mitigated_triggers_resolved_update(self):
        report = VoluntaryHazardReportFactory(is_resolved=False)
        risk1 = RiskFactory(report=report, condition="MITIGATED")
        risk2 = RiskFactory(report=report, condition="UNMITIGATED")
        risk2.condition = "MITIGATED"
        risk2.save(update_fields=["condition"])
        report.refresh_from_db()
        assert report.is_resolved is True

    def test_saving_mitigation_action_completed_triggers_resolved_check(self):
        report = VoluntaryHazardReportFactory(is_resolved=False)
        risk = RiskFactory(report=report, condition="UNMITIGATED")
        action = MitigationActionFactory(risk=risk, status="PENDING")
        action.status = "COMPLETED"
        action.save(update_fields=["status"])
        report.refresh_from_db()
        assert report.is_resolved is False
        risk.condition = "MITIGATED"
        risk.save(update_fields=["condition"])
        report.refresh_from_db()
        assert report.is_resolved is True
