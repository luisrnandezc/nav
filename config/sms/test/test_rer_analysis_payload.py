import json
from datetime import date

from django.test import TestCase

from sms.services.rer_analysis import build_rer_analysis_payload
from sms.test.factories import (
    MitigationActionEvidenceFactory,
    MitigationActionFactory,
    RiskEvaluationReportFactory,
    RiskFactory,
    StaffUserFactory,
    VoluntaryHazardReportFactory,
)


class TestRERAnalysisPayload(TestCase):
    def setUp(self):
        self.report = VoluntaryHazardReportFactory(
            code='SMS-RVP-300',
            date=date(2026, 8, 1),
            area='OPERATIONS',
            description='Incursión de una aeronave en un área restringida.',
            is_processed=True,
        )
        self.priority_risk = RiskFactory(
            report=self.report,
            description='Colisión con personal en plataforma.',
            pre_evaluation_severity='A',
            pre_evaluation_probability='3',
        )
        self.other_risk = RiskFactory(
            report=self.report,
            description='Daños menores a equipos de apoyo.',
            pre_evaluation_severity='D',
            pre_evaluation_probability='4',
        )
        self.rer = RiskEvaluationReportFactory(
            report=self.report,
            selected_risk=self.priority_risk,
            registration_date=date(2026, 8, 2),
            sms_user_fullname='Ana SMS',
            dir_user_fullname='Luis Director',
            hazard_description='Movimiento no autorizado en plataforma.',
            hazard_source='VHR',
            hazard_type='HUM',
            hazard_area='PLATFORM',
            hazard_causes='Falta de coordinación.',
            defenses='Procedimientos operacionales publicados.',
        )

    def add_action(self, risk, *, description, evidence_description):
        responsible = StaffUserFactory(
            first_name='María',
            last_name='Pérez',
        )
        action = MitigationActionFactory(
            risk=risk,
            description=description,
            responsible=responsible,
            status='COMPLETED',
            due_date=date(2026, 8, 10),
            follow_date=date(2026, 8, 20),
            notes='Verificar cumplimiento durante el turno de mañana.',
        )
        evidence = MitigationActionEvidenceFactory(
            mitigation_action=action,
            description=evidence_description,
            created_at=date(2026, 8, 9),
        )
        return action, evidence

    def test_payload_contains_every_risk_action_and_evidence(self):
        priority_action, priority_evidence = self.add_action(
            self.priority_risk,
            description='Instalar una barrera de acceso.',
            evidence_description='Fotografía de la barrera instalada.',
        )
        other_action, other_evidence = self.add_action(
            self.other_risk,
            description='Señalizar la ruta de los equipos.',
            evidence_description='Registro de la nueva señalización.',
        )

        payload = build_rer_analysis_payload(self.rer)

        assert [risk['id'] for risk in payload['risks']] == [
            self.priority_risk.pk,
            self.other_risk.pk,
        ]
        assert payload['risks'][0]['is_priority'] is True
        assert payload['risks'][1]['is_priority'] is False
        assert payload['risks'][0]['initial_evaluation']['severity']['value'] == 'A'
        assert payload['risks'][0]['initial_evaluation']['probability']['value'] == '3'
        assert payload['risks'][0]['mitigation_actions'][0]['id'] == priority_action.pk
        assert payload['risks'][0]['mitigation_actions'][0]['evidence']['id'] == priority_evidence.pk
        assert payload['risks'][1]['mitigation_actions'][0]['id'] == other_action.pk
        assert payload['risks'][1]['mitigation_actions'][0]['evidence']['id'] == other_evidence.pk

    def test_payload_includes_report_and_complete_action_context(self):
        action, evidence = self.add_action(
            self.priority_risk,
            description='Instalar una barrera de acceso.',
            evidence_description='Fotografía de la barrera instalada.',
        )
        self.add_action(
            self.other_risk,
            description='Señalizar la ruta de los equipos.',
            evidence_description='Registro de la nueva señalización.',
        )

        payload = build_rer_analysis_payload(self.rer)
        serialized_action = payload['risks'][0]['mitigation_actions'][0]

        assert payload['vhr'] == {
            'id': self.report.pk,
            'code': 'SMS-RVP-300',
            'date': '2026-08-01',
            'area': 'Operaciones',
            'description': 'Incursión de una aeronave en un área restringida.',
        }
        assert payload['rer']['hazard']['type'] == 'Humano'
        assert serialized_action == {
            'id': action.pk,
            'description': 'Instalar una barrera de acceso.',
            'status': 'Completado',
            'responsible': {
                'id': action.responsible_id,
                'name': 'María Pérez',
            },
            'due_date': '2026-08-10',
            'follow_up_date': '2026-08-20',
            'notes': 'Verificar cumplimiento durante el turno de mañana.',
            'evidence': {
                'id': evidence.pk,
                'description': 'Fotografía de la barrera instalada.',
                'registered_date': '2026-08-09',
            },
        }

    def test_payload_is_json_serializable(self):
        self.add_action(
            self.priority_risk,
            description='Instalar una barrera de acceso.',
            evidence_description='Fotografía de la barrera instalada.',
        )
        self.add_action(
            self.other_risk,
            description='Señalizar la ruta de los equipos.',
            evidence_description='Registro de la nueva señalización.',
        )

        payload = build_rer_analysis_payload(self.rer)

        assert json.loads(json.dumps(payload, ensure_ascii=False)) == payload
