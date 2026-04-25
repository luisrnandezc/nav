"""
Final marks under academy policy:
- Regular weighted final uses STANDARD grades and edition weights (theory_weight / practical_weight).
- Pass regular if final >= 80; otherwise pass if theory RECOVERY >= 90.
"""
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import SubjectEdition

STANDARD_PASSING_GRADE = Decimal('80')
RECOVERY_PASSING_GRADE = Decimal('90')
_WEIGHT_EPS = Decimal('0.001')


def final_weighted_grade(subject_edition: SubjectEdition, student_id: int) -> Decimal | None:
    """Weighted mean of STANDARD grades using edition weights, or None if a weighted slice is missing."""
    from .models import StudentGrade

    total = Decimal('0')
    se = subject_edition
    if se.theory_weight > _WEIGHT_EPS:
        g = (
            StudentGrade.objects.filter(
                student_id=student_id,
                subject_edition=se,
                component='theory',
                test_type='STANDARD',
            )
            .values_list('grade', flat=True)
            .first()
        )
        if g is None:
            return None
        total += Decimal(str(g)) * se.theory_weight
    if se.practical_weight > _WEIGHT_EPS:
        g = (
            StudentGrade.objects.filter(
                student_id=student_id,
                subject_edition=se,
                component='practical',
                test_type='STANDARD',
            )
            .values_list('grade', flat=True)
            .first()
        )
        if g is None:
            return None
        total += Decimal(str(g)) * se.practical_weight
    return total.quantize(Decimal('0.1'))


def student_passed_final(subject_edition: SubjectEdition, student_id: int) -> bool | None:
    """Pass if regular final >= 80; else pass if theory recovery >= 90. None if regular final incomplete."""
    from .models import StudentGrade

    final = final_weighted_grade(subject_edition, student_id)
    if final is None:
        return None
    if final >= STANDARD_PASSING_GRADE:
        return True

    theory_recovery = (
        StudentGrade.objects.filter(
            student_id=student_id,
            subject_edition=subject_edition,
            component='theory',
            test_type='RECOVERY',
        )
        .values_list('grade', flat=True)
        .first()
    )
    if theory_recovery is None:
        return False
    return Decimal(str(theory_recovery)) >= RECOVERY_PASSING_GRADE
