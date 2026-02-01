"""
SMS app – model creation and relations.
"""
from django.utils import timezone
from django.test import TestCase

from sms.models import VoluntaryHazardReport, Risk, MitigationAction
from sms.test.factories import (
    VoluntaryHazardReportFactory,
    RiskFactory,
    MitigationActionFactory,
    StaffUserFactory,
    InstructorUserFactory,
)


class TestVoluntaryHazardReportCreation(TestCase):
    """VHR creation and basic fields."""

    def test_create_vhr_with_required_fields(self):
        vhr = VoluntaryHazardReportFactory(
            description="Peligro en plataforma",
            area="PLATFORM",
        )
        assert vhr.id is not None
        assert vhr.description == "Peligro en plataforma"
        assert vhr.area == "PLATFORM"
        assert vhr.date is not None
        assert vhr.time is not None
        assert vhr.is_valid is False
        assert vhr.is_registered is False
        assert vhr.is_processed is False
        assert vhr.is_resolved is False

    def test_vhr_validity_fields(self):
        vhr = VoluntaryHazardReportFactory(is_valid=True, invalidity_reason=None)
        assert vhr.is_valid is True
        assert vhr.invalidity_reason is None

        vhr2 = VoluntaryHazardReportFactory(
            is_valid=False,
            invalidity_reason="Reporte duplicado",
        )
        assert vhr2.is_valid is False
        assert vhr2.invalidity_reason == "Reporte duplicado"

    def test_vhr_registration_sets_code_and_registered(self):
        vhr = VoluntaryHazardReportFactory(code=None, is_registered=False)
        vhr.code = f"SMS-RVP-{vhr.id}"
        vhr.is_registered = True
        vhr.save(update_fields=["code", "is_registered"])
        vhr.refresh_from_db()
        assert vhr.code == f"SMS-RVP-{vhr.id}"
        assert vhr.is_registered is True


class TestRiskCreation(TestCase):
    """Risk creation and link to VHR."""

    def test_create_risk_linked_to_vhr(self):
        vhr = VoluntaryHazardReportFactory()
        risk = RiskFactory(
            report=vhr,
            description="Riesgo de resbalón",
            status="TOLERABLE",
            condition="UNMITIGATED",
        )
        assert risk.id is not None
        assert risk.report_id == vhr.id
        assert risk.description == "Riesgo de resbalón"
        assert risk.status == "TOLERABLE"
        assert risk.condition == "UNMITIGATED"

    def test_vhr_has_risks_relation(self):
        vhr = VoluntaryHazardReportFactory()
        RiskFactory(report=vhr)
        RiskFactory(report=vhr)
        assert vhr.risks.count() == 2


class TestMitigationActionCreation(TestCase):
    """Mitigation action creation, dates, and responsible."""

    def test_create_mitigation_action_linked_to_risk(self):
        risk = RiskFactory()
        action = MitigationActionFactory(
            risk=risk,
            description="Colocar señalización",
            status="PENDING",
        )
        assert action.id is not None
        assert action.risk_id == risk.id
        assert action.description == "Colocar señalización"
        assert action.status == "PENDING"
        assert action.due_date is not None
        assert action.follow_date is not None

    def test_mitigation_action_default_dates(self):
        action = MitigationActionFactory()
        today = timezone.now().date()
        assert (action.due_date - today).days == 15
        assert (action.follow_date - today).days == 7

    def test_mitigation_action_with_responsible_staff(self):
        staff = StaffUserFactory()
        action = MitigationActionFactory(responsible=staff)
        assert action.responsible_id == staff.id
        assert action.responsible.role == "STAFF"

    def test_mitigation_action_with_responsible_instructor(self):
        instructor = InstructorUserFactory()
        action = MitigationActionFactory(responsible=instructor)
        assert action.responsible_id == instructor.id
        assert action.responsible.role == "INSTRUCTOR"

    def test_risk_has_mitigation_actions_relation(self):
        risk = RiskFactory()
        MitigationActionFactory(risk=risk)
        MitigationActionFactory(risk=risk)
        assert risk.mitigation_actions.count() == 2
