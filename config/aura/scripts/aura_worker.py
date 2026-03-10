#!/usr/bin/env python
"""
AURA AI Analysis Worker for PythonAnywhere Always-On Task

This script continuously scans simulator and flight evaluation tables (FMS app)
for unprocessed sessions and generates AURA IndividualReview records using the
OpenAI API and the AURA prompt.
"""

import os
import sys
import time
import json
from datetime import timedelta

import django
from django.utils import timezone

# Add Django project to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
django_dir = os.path.join(project_dir, "..", "..")
sys.path.insert(0, django_dir)

# Set Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# Import Django models and functions AFTER django.setup()
from accounts.models import User  # noqa: E402
from aura.models import IndividualReview, GlobalReview  # noqa: E402
from aura.views import (  # noqa: E402
    run_ai_analysis_for_individual_review,
    generate_incremental_global_review_for_student,
)
from fms.models import (  # noqa: E402
    SimEvaluation,
    FlightEvaluation0_100,
    FlightEvaluation100_120,
    FlightEvaluation120_170,
)


def build_session_comment(session, session_type: str) -> str:
    """
    Build a rich but compact text block from an FMS session to feed into AURA.
    """
    # Common header elements
    header_parts = [
        f"Tipo: {session_type}",
    ]

    # Session date
    session_date = getattr(session, "session_date", None)
    if session_date:
        header_parts.append(f"Fecha: {session_date}")

    # Student and instructor names (if available)
    student_first = getattr(session, "student_first_name", "") or ""
    student_last = getattr(session, "student_last_name", "") or ""
    if student_first or student_last:
        header_parts.append(f"Alumno: {student_first} {student_last}".strip())

    instructor_first = getattr(session, "instructor_first_name", "") or ""
    instructor_last = getattr(session, "instructor_last_name", "") or ""
    if instructor_first or instructor_last:
        header_parts.append(f"Instructor: {instructor_first} {instructor_last}".strip())

    # Overall grade if present
    session_grade = getattr(session, "session_grade", None)
    if session_grade:
        header_parts.append(f"Nota global: {session_grade}")

    header = " | ".join(h for h in header_parts if h)

    comments = getattr(session, "comments", "") or ""
    # Combine header and comments, marking clearly what is what
    full_text = f"[META] {header}\n[COMENTARIO] {comments}"
    return full_text.strip()


def get_or_none_user_by_national_id(national_id: int, role: str) -> User | None:
    try:
        return User.objects.get(national_id=national_id, role=role)
    except User.DoesNotExist:
        return None


def process_single_session(session, session_type: str) -> bool:
    """
    Process one FMS session (sim or flight) and create an IndividualReview.
    """
    # Avoid re-processing
    if getattr(session, "aura_processed", False):
        return False

    # Skip if there are no comments
    comments = getattr(session, "comments", "") or ""
    if not comments.strip():
        session.aura_processed = True
        session.save(update_fields=["aura_processed"])
        return False

    print(f"[{timezone.now()}] Processing {session_type} session id={session.id}")

    # Resolve student and instructor users via national_id
    student_user = None
    instructor_user = None

    student_id = getattr(session, "student_id", None)
    if student_id:
        student_user = get_or_none_user_by_national_id(student_id, User.Role.STUDENT)

    instructor_id = getattr(session, "instructor_id", None)
    if instructor_id:
        instructor_user = get_or_none_user_by_national_id(instructor_id, User.Role.INSTRUCTOR)

    if not student_user:
        print(f"[{timezone.now()}] Skipping session id={session.id}: student user not found.")
        session.aura_processed = True
        session.save(update_fields=["aura_processed"])
        return False

    # Build input text
    session_comment_text = build_session_comment(session, session_type=session_type)

    # Call OpenAI via AURA helper
    response_text = run_ai_analysis_for_individual_review(
        session_comment=session_comment_text,
        session_type=session_type,
    )

    print(
        "[{}] AURA API response type: {}, length: {}, preview: '{}'".format(
            timezone.now(),
            type(response_text).__name__,
            len(str(response_text)) if response_text else 0,
            str(response_text)[:100] if response_text else "None",
        )
    )

    if not response_text or not isinstance(response_text, str):
        print(f"[{timezone.now()}] Empty or invalid response for session id={session.id}")
        session.aura_processed = True
        session.save(update_fields=["aura_processed"])
        return False

    if response_text.startswith("Error:"):
        print(f"[{timezone.now()}] OpenAI error for session id={session.id}: {response_text}")
        session.aura_processed = True
        session.save(update_fields=["aura_processed"])
        return False

    # Parse JSON response
    try:
        parsed_response = json.loads(response_text)
    except (json.JSONDecodeError, ValueError) as e:
        print(
            "[{}] Invalid JSON response for session id={}: {} (preview='{}')".format(
                timezone.now(),
                session.id,
                e,
                response_text[:200] if len(response_text) > 200 else response_text,
            )
        )
        session.aura_processed = True
        session.save(update_fields=["aura_processed"])
        return False

    if not isinstance(parsed_response, dict):
        print(
            "[{}] Unexpected JSON type for session id={}: expected dict, got {}".format(
                timezone.now(),
                session.id,
                type(parsed_response).__name__,
            )
        )
        session.aura_processed = True
        session.save(update_fields=["aura_processed"])
        return False

    # Create IndividualReview record
    individual_review = IndividualReview.objects.create(
        student=student_user,
        instructor=instructor_user,
        source_comment_text=comments,
        ai_status=IndividualReview.STATUS_COMPLETED,
        ai_raw_response=response_text,
        ai_result=parsed_response,
    )

    print(
        "[{}] Created IndividualReview id={} for session id={}".format(
            timezone.now(),
            individual_review.id,
            session.id,
        )
    )

    # Mark session as processed and link to the created review
    session.aura_processed = True
    if hasattr(session, "aura_review"):
        session.aura_review = individual_review
        session.save(update_fields=["aura_processed", "aura_review"])
    else:
        session.save(update_fields=["aura_processed"])

    # Refresh the student's default global profile using the new individual review.
    try:
        start_date = timezone.now() - timedelta(days=90)
        global_review = generate_incremental_global_review_for_student(
            student_user,
            individual_review,
            start_date=start_date,
            end_date=None,
            scope_type=GlobalReview.SCOPE_OVERALL,
            time_window=GlobalReview.WINDOW_LAST_90_DAYS,
        )
        if global_review:
            print(
                "[{}] Updated GlobalReview id={} for student id={} after session id={}".format(
                    timezone.now(),
                    global_review.id,
                    student_user.id,
                    session.id,
                )
            )
        else:
            print(
                "[{}] No GlobalReview snapshot was created/updated for student id={} after session id={}".format(
                    timezone.now(),
                    student_user.id,
                    session.id,
                )
            )
    except Exception as e:
        print(
            "[{}] Error updating global review for student id={} after session id={}: {}".format(
                timezone.now(),
                student_user.id,
                session.id,
                e,
            )
        )

    return True


def process_pending_sessions():
    """
    Find and process all pending (aura_processed=False) sessions.
    """
    # Sim sessions
    sim_pending = SimEvaluation.objects.filter(aura_processed=False).order_by("session_date", "id")
    # Flight sessions (three ranges)
    f0_pending = FlightEvaluation0_100.objects.filter(aura_processed=False).order_by("session_date", "id")
    f1_pending = FlightEvaluation100_120.objects.filter(aura_processed=False).order_by("session_date", "id")
    f2_pending = FlightEvaluation120_170.objects.filter(aura_processed=False).order_by("session_date", "id")

    total_pending = (
        sim_pending.count() + f0_pending.count() + f1_pending.count() + f2_pending.count()
    )
    print("[{}] Found {} pending sessions for AURA".format(timezone.now(), total_pending))

    for session in sim_pending:
        process_single_session(session, session_type="SIM")
        time.sleep(3)

    for session in f0_pending:
        process_single_session(session, session_type="FLIGHT")
        time.sleep(3)

    for session in f1_pending:
        process_single_session(session, session_type="FLIGHT")
        time.sleep(3)

    for session in f2_pending:
        process_single_session(session, session_type="FLIGHT")
        time.sleep(3)


def main_worker_loop():
    """
    Main worker loop that continuously scans for pending sessions.
    """
    print("[{}] AURA AI Worker started".format(timezone.now()))
    print("[{}] Scanning for pending sessions every 30 seconds...".format(timezone.now()))

    while True:
        try:
            process_pending_sessions()
            time.sleep(30)
        except KeyboardInterrupt:
            print("[{}] AURA Worker stopped by user".format(timezone.now()))
            break
        except Exception as e:
            print("[{}] AURA Worker error: {}".format(timezone.now(), str(e)))
            time.sleep(60)


if __name__ == "__main__":
    main_worker_loop()

