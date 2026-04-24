"""
Final marks from weighted components and per-component effective grades.

Each subject edition has exactly two components (theory + practical). Effective grade for a
component is max(standard, recovery) when both exist; otherwise whichever exists.
Final weighted grade: sum(effective_i * weight_i) for components with weight > 0 only (so a
practical at weight 0 does not require a practical score for the final).
"""
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db.models import Sum

if TYPE_CHECKING:
    from .models import SubjectEdition, SubjectEditionGradingComponent

SUM_TOLERANCE = Decimal('0.001')


def grading_components_weight_sum(subject_edition: SubjectEdition) -> Decimal:
    """Sum of weights for all grading components of this subject edition."""
    total = subject_edition.grading_components.aggregate(s=Sum('weight'))['s']
    return total if total is not None else Decimal('0')


def ensure_theory_practical_components(subject_edition: SubjectEdition) -> None:
    """Ensure theory (default weight 1) and practical (default weight 0) rows exist; never overwrites existing weights."""
    from .models import SubjectEditionGradingComponent

    SubjectEditionGradingComponent.objects.get_or_create(
        subject_edition=subject_edition,
        code='theory',
        defaults={
            'kind': 'THEORY',
            'label': 'Examen teórico',
            'weight': Decimal('1.0'),
            'order': 0,
        },
    )
    SubjectEditionGradingComponent.objects.get_or_create(
        subject_edition=subject_edition,
        code='practical',
        defaults={
            'kind': 'PRACTICAL',
            'label': 'Evaluación práctica',
            'weight': Decimal('0'),
            'order': 1,
        },
    )


def effective_grade_for_component(
    student_id: int,
    component: SubjectEditionGradingComponent,
) -> Decimal | None:
    """
    Numeric score used in the final for this component (max of standard and recovery rows).
    """
    from .models import StudentGrade

    grades = StudentGrade.objects.filter(student_id=student_id, component=component)
    standard = grades.filter(test_type='STANDARD').values_list('grade', flat=True).first()
    recovery = grades.filter(test_type='RECOVERY').values_list('grade', flat=True).first()
    if standard is None and recovery is None:
        return None
    if standard is None:
        return Decimal(str(recovery))
    if recovery is None:
        return Decimal(str(standard))
    return max(Decimal(str(standard)), Decimal(str(recovery)))


def final_weighted_grade(subject_edition: SubjectEdition, student_id: int) -> Decimal | None:
    """
    Weighted final mark, or None if any component with weight > 0 has no standard/recovery grade yet.
    """
    components = list(subject_edition.grading_components.order_by('order', 'code'))
    if not components:
        return None
    total = Decimal('0')
    for comp in components:
        if comp.weight is None or comp.weight <= Decimal('0'):
            continue
        eg = effective_grade_for_component(student_id, comp)
        if eg is None:
            return None
        total += eg * comp.weight
    return total.quantize(Decimal('0.1'))


def student_passed_final(subject_edition: SubjectEdition, student_id: int) -> bool | None:
    """
    Whether the weighted final meets the subject passing threshold.

    If the student has any recovery grade row for this edition, uses recovery_passing_grade on the
    final; otherwise uses passing_grade. Returns None if the final cannot be computed yet.
    """
    from .models import StudentGrade

    final = final_weighted_grade(subject_edition, student_id)
    if final is None:
        return None
    st = subject_edition.subject_type
    has_recovery = StudentGrade.objects.filter(
        student_id=student_id,
        subject_edition=subject_edition,
        test_type='RECOVERY',
    ).exists()
    threshold = st.recovery_passing_grade if has_recovery else st.passing_grade
    return final >= Decimal(threshold)
