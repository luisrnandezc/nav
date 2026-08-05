"""Build the input consumed by SARA's RER residual-risk analysis."""

from typing import Any

from django.db.models import Prefetch

from sms.models import MitigationAction, RiskEvaluationReport


def build_rer_analysis_payload(rer: RiskEvaluationReport) -> dict[str, Any]:
    """Return a deterministic, JSON-safe snapshot of an RER and all its risks.

    This function deliberately performs no validation, database writes, or AI
    calls. Readiness is enforced before the RER form is displayed; this layer is
    only responsible for representing the approved report data faithfully.
    """
    report = rer.report
    actions = MitigationAction.objects.order_by('pk').select_related(
        'responsible',
        'evidence',
    )
    risks = report.risks.order_by('pk').prefetch_related(
        Prefetch(
            'mitigation_actions',
            queryset=actions,
            to_attr='analysis_actions',
        ),
    )

    return {
        'rer': {
            'id': rer.pk,
            'registration_date': rer.registration_date.isoformat(),
            'sms_coordinator': rer.sms_user_fullname,
            'director': rer.dir_user_fullname,
            'hazard': {
                'description': rer.hazard_description,
                'source': rer.get_hazard_source_display(),
                'type': rer.get_hazard_type_display(),
                'area': rer.get_hazard_area_display(),
                'possible_causes': rer.hazard_causes,
                'existing_defenses': rer.defenses,
            },
        },
        'vhr': {
            'id': report.pk,
            'code': report.code,
            'date': report.date.isoformat(),
            'area': report.get_area_display(),
            'description': report.description,
        },
        'risks': [
            _serialize_risk(risk, priority_risk_id=rer.selected_risk_id)
            for risk in risks
        ],
    }


def _serialize_risk(risk, *, priority_risk_id: int) -> dict[str, Any]:
    return {
        'id': risk.pk,
        'description': risk.description,
        # Priority is contextual only; SARA must evaluate every listed risk.
        'is_priority': risk.pk == priority_risk_id,
        'initial_evaluation': {
            'severity': {
                'value': risk.pre_evaluation_severity,
                'label': risk.get_pre_evaluation_severity_display(),
            },
            'probability': {
                'value': risk.pre_evaluation_probability,
                'label': risk.get_pre_evaluation_probability_display(),
            },
        },
        'mitigation_actions': [
            _serialize_action(action) for action in risk.analysis_actions
        ],
    }


def _serialize_action(action) -> dict[str, Any]:
    responsible = action.responsible
    evidence = action.evidence

    return {
        'id': action.pk,
        'description': action.description,
        'status': action.get_status_display(),
        'responsible': {
            'id': responsible.pk,
            'name': responsible.get_full_name() or responsible.get_username(),
        },
        'due_date': action.due_date.isoformat(),
        'follow_up_date': action.follow_date.isoformat(),
        'notes': action.notes or '',
        'evidence': {
            'id': evidence.pk,
            'description': evidence.description,
            'registered_date': evidence.created_at.isoformat(),
        },
    }
