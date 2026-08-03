from dataclasses import dataclass

from .models import VoluntaryHazardReport


@dataclass(frozen=True)
class RERReadinessResult:
    is_ready: bool
    errors: tuple[str, ...]


def evaluate_rer_readiness(report: VoluntaryHazardReport) -> RERReadinessResult:
    """Return whether a VHR contains all data required to create its RER."""
    errors = []

    if not report.is_processed:
        errors.append('El RVP debe estar procesado antes de generar el RER.')

    if not report.code:
        errors.append('El RVP debe tener un código único antes de generar el RER.')

    risks = list(
        report.risks.prefetch_related(
            'mitigation_actions__responsible',
            'mitigation_actions__evidence',
        ).order_by('id')
    )

    if not risks:
        errors.append('El RVP debe tener al menos un riesgo registrado.')

    for risk in risks:
        risk_label = f'Riesgo {risk.id}'

        if risk.pre_evaluation_severity == '0':
            errors.append(f'{risk_label}: debe tener una severidad inicial definida.')

        if risk.pre_evaluation_probability == '0':
            errors.append(f'{risk_label}: debe tener una probabilidad inicial definida.')

        actions = list(risk.mitigation_actions.all())
        if not actions:
            errors.append(f'{risk_label}: debe tener al menos una MMR registrada.')
            continue

        for action in actions:
            action_label = f'MMR {action.id} del riesgo {risk.id}'

            if not action.responsible_id:
                errors.append(f'{action_label}: debe tener un responsable asignado.')
            if not action.due_date:
                errors.append(f'{action_label}: debe tener una fecha límite.')
            if not action.follow_date:
                errors.append(f'{action_label}: debe tener una fecha de seguimiento.')
            if not hasattr(action, 'evidence'):
                errors.append(f'{action_label}: debe tener una evidencia registrada.')

    return RERReadinessResult(is_ready=not errors, errors=tuple(errors))
