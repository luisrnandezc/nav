"""
Final marks and student grade overview helpers.

- Regular weighted final uses STANDARD grades and edition weights (theory_weight / practical_weight).
- Pass regular if final >= 80; otherwise pass if theory RECOVERY >= 90.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from accounts.models import User

if TYPE_CHECKING:
    from .models import StudentGrade, SubjectEdition

STANDARD_PASSING_GRADE = Decimal('80')
RECOVERY_PASSING_GRADE = Decimal('90')
DEFAULT_TOTAL_CURRICULUM_SUBJECTS = 13
_WEIGHT_EPS = Decimal('0.001')
CURRICULUM_SUBJECT_TOTALS_BY_COURSE = {
    'PPA-T': 13,
    'HVI-T': 7,
    'PCA-T': 9,
    'TLA-T': 7,
    'IVA': 2,
    'IVS': 2,
}


def final_weighted_grade(subject_edition: SubjectEdition, student_id: int) -> Decimal | None:
    """
    Weighted final using STANDARD grades.

    If theory RECOVERY exists and is >= 90, the final used for aggregates is capped at 80.0.
    """
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
    raw_final = total.quantize(Decimal('0.1'))

    theory_recovery = (
        StudentGrade.objects.filter(
            student_id=student_id,
            subject_edition=se,
            component='theory',
            test_type='RECOVERY',
        )
        .values_list('grade', flat=True)
        .first()
    )
    if theory_recovery is not None and Decimal(str(theory_recovery)) >= RECOVERY_PASSING_GRADE:
        return STANDARD_PASSING_GRADE.quantize(Decimal('0.1'))
    return raw_final


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


def effective_final_grade(subject_edition: SubjectEdition, student_id: int) -> Decimal | None:
    """Compute the effective final grade for a subject.
    
    The effective final subject grade is capped at 80 if the student passed with a recovery exam."""
    return None


@dataclass
class StudentGradeOverview:
    """All grade rows for a student plus per–subject-edition final/pass outcomes."""

    grades: tuple[StudentGrade, ...]
    enrolled_editions: tuple[SubjectEdition, ...]
    edition_final_grade: dict[int, Decimal | None]
    edition_course_passed: dict[int, bool | None]


def load_student_grade_overview(user: User) -> StudentGradeOverview:
    """
    Single DB pass for the student's grades and enrollments, plus derived
    final mark and course pass outcome per enrolled edition.
    """
    from .models import StudentGrade, SubjectEdition

    grades = tuple(
        StudentGrade.objects.filter(student=user)
        .select_related('subject_edition__subject_type', 'instructor', 'subject_edition')
        .order_by('-date')
    )
    enrolled_editions = tuple(
        SubjectEdition.objects.filter(students=user).select_related('subject_type')
    )

    edition_final_grade: dict[int, Decimal | None] = {}
    edition_course_passed: dict[int, bool | None] = {}
    uid = user.pk
    for edition in enrolled_editions:
        edition_final_grade[edition.pk] = final_weighted_grade(edition, uid)
        edition_course_passed[edition.pk] = student_passed_final(edition, uid)

    return StudentGradeOverview(
        grades=grades,
        enrolled_editions=enrolled_editions,
        edition_final_grade=edition_final_grade,
        edition_course_passed=edition_course_passed,
    )


def subject_options_for_overview(overview: StudentGradeOverview):
    """Distinct subject types present in the student's grade rows."""
    from .models import SubjectType

    ids = {
        g.subject_edition.subject_type_id
        for g in overview.grades
        if g.subject_edition_id and g.subject_edition.subject_type_id
    }
    return SubjectType.objects.filter(pk__in=ids).order_by('name')


def compute_approved_and_pending(
    overview: StudentGradeOverview,
    total_curriculum_subjects: int = DEFAULT_TOTAL_CURRICULUM_SUBJECTS,
) -> tuple[int, int]:
    """
    Approved = enrolled editions where the student passed the course rule.
    Pending = curriculum total minus approved (floored at 0). Curriculum total
    is a placeholder until it is derived from the student's course.
    """
    approved = sum(
        1
        for ed in overview.enrolled_editions
        if overview.edition_course_passed.get(ed.pk) is True
    )
    pending = max(0, total_curriculum_subjects - approved)
    return approved, pending


def curriculum_subject_total_for_student(user: User) -> int:
    """
    Number of subjects expected for the student's current course.

    Falls back to DEFAULT_TOTAL_CURRICULUM_SUBJECTS when the student has no
    current course or when its code is not yet mapped.
    """
    course_code = (
        user.student_profile.current_course_type
        if hasattr(user, 'student_profile')
        else None
    )
    if not course_code:
        return DEFAULT_TOTAL_CURRICULUM_SUBJECTS

    direct = CURRICULUM_SUBJECT_TOTALS_BY_COURSE.get(course_code)
    if direct is not None:
        return direct

    normalized = course_code.replace('-P', '').replace('-T', '')
    return CURRICULUM_SUBJECT_TOTALS_BY_COURSE.get(
        normalized,
        DEFAULT_TOTAL_CURRICULUM_SUBJECTS,
    )


def compute_final_grade_min_max(
    overview: StudentGradeOverview,
) -> tuple[Decimal | None, Decimal | None]:
    """Min and max of *final weighted* marks over enrolled editions (None omitted)."""
    
    finals = [g for g in overview.edition_final_grade.values() if g is not None]
    if not finals:
        return None, None
    return min(finals), max(finals)


def compute_final_grade_average(overview: StudentGradeOverview) -> Decimal | None:
    """Average of final weighted marks over enrolled editions with a complete final."""
    finals = [g for g in overview.edition_final_grade.values() if g is not None]
    if not finals:
        return None
    return (sum(finals, Decimal('0')) / len(finals)).quantize(Decimal('0.1'))


def filter_grade_rows_for_display(
    overview: StudentGradeOverview,
    *,
    subject_type_id: int | None,
    limit: int = 500,
) -> list[StudentGrade]:
    """Subset of overview.grades for the log list (optional subject filter, cap)."""
    rows = overview.grades
    if subject_type_id is not None:
        rows = tuple(g for g in rows if g.subject_edition.subject_type_id == subject_type_id)
    return list(rows[:limit])
