"""Data preparation for the Risk Evaluation Report PDF."""

from django.db.models import Prefetch

from sms.models import MitigationAction, Risk, RiskEvaluationReport


INTOLERABLE_INDICES = {'A5', 'B5', 'C5', 'A4', 'B4', 'A3'}
TOLERABLE_INDICES = {
    'D5', 'E5', 'C4', 'D4', 'E4', 'B3',
    'C3', 'D3', 'A2', 'B2', 'C2', 'A1',
}
ACCEPTABLE_INDICES = {'E3', 'D2', 'E2', 'B1', 'C1', 'D1', 'E1'}

TOLERABILITY_LABELS = {
    'INTOLERABLE': 'Intolerable',
    'TOLERABLE': 'Tolerable',
    'ACCEPTABLE': 'Aceptable',
}


def classify_risk_index(index):
    """Return the established SMS tolerability classification for an index."""
    if index in INTOLERABLE_INDICES:
        code = 'INTOLERABLE'
    elif index in TOLERABLE_INDICES:
        code = 'TOLERABLE'
    elif index in ACCEPTABLE_INDICES:
        code = 'ACCEPTABLE'
    else:
        raise ValueError(f'Invalid risk matrix index: {index}')

    return {
        'code': code,
        'label': TOLERABILITY_LABELS[code],
    }


def build_rer_pdf_context(rer):
    """Build the complete, template-ready context for one reviewed RER."""
    if not rer.pk:
        raise ValueError('The RER must be saved before building its PDF context.')

    actions = MitigationAction.objects.select_related(
        'responsible',
        'evidence',
    ).order_by('pk')
    risks = Risk.objects.prefetch_related(
        Prefetch('mitigation_actions', queryset=actions, to_attr='pdf_actions'),
    ).order_by('pk')
    rer = (
        RiskEvaluationReport.objects
        .select_related('report', 'selected_risk', 'reviewed_by')
        .prefetch_related(Prefetch('report__risks', queryset=risks))
        .get(pk=rer.pk)
    )

    if rer.analysis_status != 'REVIEWED':
        raise ValueError('Only a reviewed RER can be prepared for PDF generation.')
    if not rer.reviewed_by_id or not rer.reviewed_at:
        raise ValueError('The reviewed RER is missing its review metadata.')

    severity_labels = dict(Risk.SEVERITY_CHOICES)
    probability_labels = dict(Risk.PROBABILITY_CHOICES)
    risk_entries = []
    action_entries = []

    for risk_number, risk in enumerate(rer.report.risks.all(), start=1):
        initial_index = risk.pre_evaluation()
        residual_index = risk.post_evaluation()
        risk_entries.append({
            'number': risk_number,
            'id': risk.pk,
            'description': risk.description,
            'is_priority': risk.pk == rer.selected_risk_id,
            'initial': {
                'severity': risk.pre_evaluation_severity,
                'severity_label': severity_labels[risk.pre_evaluation_severity],
                'probability': risk.pre_evaluation_probability,
                'probability_label': probability_labels[
                    risk.pre_evaluation_probability
                ],
                'index': initial_index,
                'tolerability': classify_risk_index(initial_index),
            },
            'residual': {
                'severity': risk.post_evaluation_severity,
                'severity_label': severity_labels[risk.post_evaluation_severity],
                'probability': risk.post_evaluation_probability,
                'probability_label': probability_labels[
                    risk.post_evaluation_probability
                ],
                'index': residual_index,
                'tolerability': classify_risk_index(residual_index),
                'justification': risk.post_evaluation_justification,
            },
        })

        for action in risk.pdf_actions:
            responsible_name = (
                action.responsible.get_full_name()
                or action.responsible.get_username()
            )
            action_entries.append({
                'number': len(action_entries) + 1,
                'id': action.pk,
                'risk_id': risk.pk,
                'risk_number': risk_number,
                'description': action.description,
                'responsible': responsible_name,
                'due_date': action.due_date,
                'follow_date': action.follow_date,
                'evidence': action.evidence.description,
            })

    reviewer_name = rer.reviewed_by.get_full_name() or rer.reviewed_by.get_username()
    return {
        'document': {
            'rer_id': rer.pk,
            'reference_code': rer.report.code,
            'registration_date': rer.registration_date,
            'reviewed_at': rer.reviewed_at,
        },
        'source_report': {
            'id': rer.report_id,
            'code': rer.report.code,
            'description': rer.report.description,
            'date': rer.report.date,
        },
        'hazard': {
            'description': rer.hazard_description,
            'source': rer.get_hazard_source_display(),
            'type': rer.get_hazard_type_display(),
            'area': rer.get_hazard_area_display(),
            'possible_causes': rer.hazard_causes,
            'existing_defenses': rer.defenses,
        },
        'priority_risk_id': rer.selected_risk_id,
        'risks': risk_entries,
        'mitigation_actions': action_entries,
        'approvals': {
            'sms_coordinator': rer.sms_user_fullname,
            'director': rer.dir_user_fullname,
            'reviewed_by': reviewer_name,
        },
    }
