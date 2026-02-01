"""
SMS app – school status from unmitigated risk counts (INTOLERABLE / TOLERABLE / ACCEPTABLE).
"""
from django.test import TestCase

from sms.models import Risk
from sms.views import get_sms_school_status
from sms.test.factories import VoluntaryHazardReportFactory, RiskFactory


def _unmitigated_risks_with_statuses(*statuses):
    """Create a report with unmitigated risks with given statuses; return queryset of those risks."""
    report = VoluntaryHazardReportFactory(is_processed=True)
    for status in statuses:
        RiskFactory(report=report, condition="UNMITIGATED", status=status)
    return Risk.objects.filter(report=report, condition="UNMITIGATED")


class TestGetSmsSchoolStatus(TestCase):
    """get_sms_school_status from unmitigated risks."""

    def test_critical_when_any_intolerable(self):
        risks = _unmitigated_risks_with_statuses("INTOLERABLE")
        assert get_sms_school_status(risks) == "CRÍTICO"

    def test_critical_when_intolerable_and_tolerable(self):
        risks = _unmitigated_risks_with_statuses("INTOLERABLE", "TOLERABLE")
        assert get_sms_school_status(risks) == "CRÍTICO"

    def test_precaution_when_tolerable_few(self):
        risks = _unmitigated_risks_with_statuses("TOLERABLE", "TOLERABLE")
        assert get_sms_school_status(risks) == "PRECAUCIÓN"

    def test_precaution_when_tolerable_four(self):
        risks = _unmitigated_risks_with_statuses(
            "TOLERABLE", "TOLERABLE", "TOLERABLE", "TOLERABLE"
        )
        assert get_sms_school_status(risks) == "PRECAUCIÓN"

    def test_critical_when_tolerable_more_than_four(self):
        risks = _unmitigated_risks_with_statuses(
            "TOLERABLE", "TOLERABLE", "TOLERABLE", "TOLERABLE", "TOLERABLE"
        )
        assert get_sms_school_status(risks) == "CRÍTICO"

    def test_safe_when_only_acceptable(self):
        risks = _unmitigated_risks_with_statuses("ACCEPTABLE", "ACCEPTABLE")
        assert get_sms_school_status(risks) == "SEGURO"

    def test_safe_when_no_risks(self):
        report = VoluntaryHazardReportFactory(is_processed=True)
        risks = Risk.objects.filter(report=report, condition="UNMITIGATED")
        assert get_sms_school_status(risks) == "SEGURO"

    def test_safe_when_only_not_evaluated(self):
        risks = _unmitigated_risks_with_statuses("NOT_EVALUATED")
        assert get_sms_school_status(risks) == "SEGURO"
