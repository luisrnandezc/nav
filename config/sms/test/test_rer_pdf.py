from django.test import TestCase
from django.utils import timezone

from sms.rer_pdf import build_rer_pdf_context, classify_risk_index
from sms.test.factories import (
    MitigationActionEvidenceFactory,
    MitigationActionFactory,
    RiskEvaluationReportFactory,
    RiskFactory,
    StaffUserFactory,
    VoluntaryHazardReportFactory,
)


class TestRERPDFContext(TestCase):
    def setUp(self):
        self.reviewer = StaffUserFactory(
            first_name='María',
            last_name='Pérez',
        )
        self.report = VoluntaryHazardReportFactory(
            code='SMS-RVP-PDF-001',
            description='Vehículo no autorizado en plataforma.',
            is_processed=True,
            area='OPERATIONS',
        )
        self.priority_risk = RiskFactory(
            report=self.report,
            description='Colisión con una aeronave.',
            pre_evaluation_severity='B',
            pre_evaluation_probability='4',
            post_evaluation_severity='B',
            post_evaluation_probability='2',
            post_evaluation_justification='El control reduce la exposición.',
        )
        self.second_risk = RiskFactory(
            report=self.report,
            description='Lesión del personal.',
            pre_evaluation_severity='C',
            pre_evaluation_probability='3',
            post_evaluation_severity='C',
            post_evaluation_probability='1',
            post_evaluation_justification='La señalización limita el acceso.',
        )
        self.first_action = self._create_action(
            self.priority_risk,
            'Controlar el acceso a la plataforma.',
            'Registro diario de autorizaciones.',
        )
        self.second_action = self._create_action(
            self.second_risk,
            'Instalar señalización preventiva.',
            'Fotografía de la señalización instalada.',
        )
        self.rer = RiskEvaluationReportFactory(
            report=self.report,
            selected_risk=self.priority_risk,
            analysis_status='REVIEWED',
            reviewed_by=self.reviewer,
            reviewed_at=timezone.now(),
            sms_user_fullname='Coordinador SMS',
            dir_user_fullname='Director General',
            hazard_description='Ingreso no coordinado a plataforma.',
            hazard_source='VHR',
            hazard_type='ORG',
            hazard_area='OPERATIONS',
            hazard_causes='Falta de control de acceso.',
            defenses='Procedimiento de circulación vigente.',
        )

    def _create_action(self, risk, description, evidence):
        action = MitigationActionFactory(
            risk=risk,
            description=description,
            responsible=self.reviewer,
        )
        MitigationActionEvidenceFactory(
            mitigation_action=action,
            description=evidence,
        )
        return action

    def test_context_contains_every_pdf_section_and_related_record(self):
        context = build_rer_pdf_context(self.rer)

        assert context['document']['reference_code'] == self.report.code
        assert context['source_report']['description'] == self.report.description
        assert context['hazard']['description'] == self.rer.hazard_description
        assert context['hazard']['possible_causes'] == self.rer.hazard_causes
        assert context['hazard']['existing_defenses'] == self.rer.defenses
        assert context['priority_risk_id'] == self.priority_risk.pk

        assert len(context['risks']) == 2
        priority = context['risks'][0]
        assert priority['id'] == self.priority_risk.pk
        assert priority['is_priority'] is True
        assert priority['initial']['index'] == 'B4'
        assert priority['initial']['tolerability']['code'] == 'INTOLERABLE'
        assert priority['residual']['index'] == 'B2'
        assert priority['residual']['tolerability']['code'] == 'TOLERABLE'
        assert priority['residual']['justification'] == (
            self.priority_risk.post_evaluation_justification
        )

        second = context['risks'][1]
        assert second['id'] == self.second_risk.pk
        assert second['is_priority'] is False
        assert second['residual']['index'] == 'C1'
        assert second['residual']['tolerability']['code'] == 'ACCEPTABLE'

        assert len(context['mitigation_actions']) == 2
        first_action = context['mitigation_actions'][0]
        assert first_action['id'] == self.first_action.pk
        assert first_action['risk_id'] == self.priority_risk.pk
        assert first_action['responsible'] == self.reviewer.get_full_name()
        assert first_action['due_date'] == self.first_action.due_date
        assert first_action['follow_date'] == self.first_action.follow_date
        assert first_action['evidence'] == self.first_action.evidence.description
        assert context['mitigation_actions'][1]['id'] == self.second_action.pk

        assert context['approvals'] == {
            'sms_coordinator': 'Coordinador SMS',
            'director': 'Director General',
            'reviewed_by': self.reviewer.get_full_name(),
        }

    def test_unreviewed_rer_is_rejected(self):
        self.rer.analysis_status = 'READY_FOR_REVIEW'
        self.rer.save(update_fields=['analysis_status'])

        with self.assertRaisesRegex(ValueError, 'Only a reviewed RER'):
            build_rer_pdf_context(self.rer)

    def test_reviewed_rer_without_review_metadata_is_rejected(self):
        self.rer.reviewed_by = None
        self.rer.reviewed_at = None
        self.rer.save(update_fields=['reviewed_by', 'reviewed_at'])

        with self.assertRaisesRegex(ValueError, 'missing its review metadata'):
            build_rer_pdf_context(self.rer)

    def test_matrix_classification_matches_existing_sms_boundaries(self):
        assert classify_risk_index('A5')['code'] == 'INTOLERABLE'
        assert classify_risk_index('B2')['code'] == 'TOLERABLE'
        assert classify_risk_index('E1')['code'] == 'ACCEPTABLE'

        with self.assertRaisesRegex(ValueError, 'Invalid risk matrix index'):
            classify_risk_index('-')
