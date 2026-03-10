import json
import logging
import os
import sys
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from openai import OpenAI

from accounts.models import StudentProfile
from .models import IndividualReview, GlobalReview


def aura_individual_review_logger():
    """
    Logger for AURA individual review AI analysis.
    """
    log_dir = os.path.join(settings.BASE_DIR, "aura", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "individual_review_ai_analysis.log")

    logger = logging.getLogger("aura_individual_review_ai_analysis")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if called multiple times
    logger.handlers = []

    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter("[AURA] %(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


def run_ai_analysis_for_individual_review(session_comment: str, session_type: str = "UNKNOWN") -> str:
    """
    Run the AURA AI analysis for a single training session comment.

    Args:
        session_comment: Raw comment text from the instructor about the session.
        session_type: "SIM", "FLIGHT" or "UNKNOWN" (used only for logging/context).

    Returns:
        The raw text response from the OpenAI API (expected to be JSON).
        In case of error, returns a string starting with "Error:".
    """
    logger = aura_individual_review_logger()

    logger.info("=" * 80)
    logger.info("Starting run_ai_analysis_for_individual_review (session_type=%s)", session_type)

    base_prompt = settings.AURA_INDIVIDUAL_REVIEW_PROMPT
    if not base_prompt:
        error_msg = "Error: AURA_INDIVIDUAL_REVIEW_PROMPT is empty or not loaded."
        logger.error(error_msg)
        return error_msg

    logger.info("AURA prompt loaded, length: %d characters", len(base_prompt))

    # Render prompt with the session comment.
    # IMPORTANT: do NOT use str.format() on the whole prompt because it contains
    # many JSON curly braces. We only want to replace the {session_comment}
    # placeholder literally.
    rendered_prompt = base_prompt.replace("{session_comment}", session_comment or "")
    logger.info("Rendered prompt length: %d characters", len(rendered_prompt))

    # Retrieve the API key from environment variables
    logger.info("Retrieving OPENAI_API_KEY from environment variables")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        error_msg = "Error: OpenAI API key not found in environment variables."
        logger.error(error_msg)
        print("[ERROR] %s", error_msg)
        return error_msg

    logger.info("API key retrieved successfully (length: %d characters)", len(api_key) if api_key else 0)

    try:
        logger.info("Attempting to initialize OpenAI client")
        client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized successfully")

        # Configure model and response options (aligned with SMS usage)
        model = "gpt-5.1"
        tools = [{"type": "web_search"}]
        reasoning = {"effort": "medium"}
        text = {"verbosity": "medium"}

        logger.info(
            "Making API request to OpenAI responses endpoint (model=%s, effort=%s, verbosity=%s)",
            model,
            reasoning["effort"],
            text["verbosity"],
        )

        response = client.responses.create(
            model=model,
            tools=tools,
            reasoning=reasoning,
            text=text,
            instructions=base_prompt,
            input=rendered_prompt,
        )

        logger.info("API request completed successfully")

        content = response.output_text
        logger.info("Response content extracted, length: %d characters", len(content) if content else 0)

        logger.info("=" * 80)
        return content

    except Exception as e:
        import traceback

        error_msg = f"Error during OpenAI operation in AURA: {e} (Type: {type(e).__name__})"
        logger.error(error_msg, exc_info=True)
        logger.error("Full traceback: %s", traceback.format_exc())
        logger.info("=" * 80)
        print("[ERROR] %s" % error_msg)
        return f"Error: {e}"


def aura_global_review_logger():
    """
    Logger for AURA global review AI analysis.
    """
    log_dir = os.path.join(settings.BASE_DIR, "aura", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "global_review_ai_analysis.log")

    logger = logging.getLogger("aura_global_review_ai_analysis")
    logger.setLevel(logging.DEBUG)

    logger.handlers = []

    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter("[AURA-GLOBAL] %(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


def _build_global_review_payload(reviews):
    payload = []
    for review in reviews:
        ai_result = review.ai_result or {}
        session_metadata = ai_result.get("session_metadata", {}) or {}
        payload.append(
            {
                "created_at": review.created_at.isoformat(),
                "session_type": session_metadata.get("session_type", "UNKNOWN"),
                "ai_result": ai_result,
            }
        )
    return payload


def _run_global_review_completion(base_prompt: str, rendered_prompt: str, request_label: str) -> str:
    logger = aura_global_review_logger()
    logger.info("Retrieving OPENAI_API_KEY from environment variables for %s", request_label)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        error_msg = "Error: OpenAI API key not found in environment variables."
        logger.error(error_msg)
        print("[ERROR] %s" % error_msg)
        return error_msg

    logger.info("API key retrieved successfully (length: %d characters)", len(api_key) if api_key else 0)

    try:
        logger.info("Attempting to initialize OpenAI client for %s", request_label)
        client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized successfully for %s", request_label)

        model = "gpt-5-nano"
        tools = [{"type": "web_search"}]
        reasoning = {"effort": "medium"}
        text = {"verbosity": "low"}

        logger.info(
            "Making API request to OpenAI responses endpoint (%s) (model=%s, effort=%s, verbosity=%s)",
            request_label,
            model,
            reasoning["effort"],
            text["verbosity"],
        )

        response = client.responses.create(
            model=model,
            tools=tools,
            reasoning=reasoning,
            text=text,
            instructions=base_prompt,
            input=rendered_prompt,
        )

        logger.info("API request for %s completed successfully", request_label)

        content = response.output_text
        logger.info(
            "%s response content length: %d characters",
            request_label,
            len(content) if content else 0,
        )
        logger.info("=" * 80)
        return content

    except Exception as e:
        import traceback

        error_msg = (
            f"Error during OpenAI operation in AURA {request_label.lower()}: {e} "
            f"(Type: {type(e).__name__})"
        )
        logger.error(error_msg, exc_info=True)
        logger.error("Full traceback: %s", traceback.format_exc())
        logger.info("=" * 80)
        print("[ERROR] %s" % error_msg)
        return f"Error: {e}"


def run_ai_analysis_for_global_review(student, reviews):
    """
    Run the AURA AI analysis to build a global review from multiple IndividualReview instances.

    Args:
        student: User instance (student).
        reviews: iterable of IndividualReview instances (already filtered for this student).

    Returns:
        Raw text response from OpenAI (expected JSON), or string starting with 'Error:'.
    """
    logger = aura_global_review_logger()

    logger.info("=" * 80)
    logger.info("Starting run_ai_analysis_for_global_review for student id=%s", getattr(student, "id", None))

    base_prompt = settings.AURA_GLOBAL_REVIEW_PROMPT
    if not base_prompt:
        error_msg = "Error: AURA_GLOBAL_REVIEW_PROMPT is empty or not loaded."
        logger.error(error_msg)
        return error_msg

    logger.info("AURA global prompt loaded, length: %d characters", len(base_prompt))

    payload = _build_global_review_payload(reviews)
    if not payload:
        error_msg = "Error: No individual reviews provided for global analysis."
        logger.error(error_msg)
        return error_msg

    student_reviews_json = json.dumps(payload, ensure_ascii=False)
    logger.info("Student reviews JSON length: %d characters", len(student_reviews_json))

    # Replace placeholder safely without using str.format on the whole prompt
    rendered_prompt = base_prompt.replace("{student_reviews_json}", student_reviews_json)
    logger.info("Rendered global prompt length: %d characters", len(rendered_prompt))

    return _run_global_review_completion(base_prompt, rendered_prompt, request_label="GLOBAL")


def run_ai_analysis_for_incremental_global_review(student, previous_global_review, new_review):
    """
    Update an existing global review snapshot by integrating one new completed individual review.
    """
    logger = aura_global_review_logger()

    logger.info("=" * 80)
    logger.info(
        "Starting run_ai_analysis_for_incremental_global_review for student id=%s, previous_global_review_id=%s, new_review_id=%s",
        getattr(student, "id", None),
        getattr(previous_global_review, "id", None),
        getattr(new_review, "id", None),
    )

    base_prompt = settings.AURA_INCREMENTAL_GLOBAL_REVIEW_PROMPT
    if not base_prompt:
        error_msg = "Error: AURA_INCREMENTAL_GLOBAL_REVIEW_PROMPT is empty or not loaded."
        logger.error(error_msg)
        return error_msg

    logger.info("AURA incremental global prompt loaded, length: %d characters", len(base_prompt))

    previous_global_review_json = json.dumps(previous_global_review.ai_result or {}, ensure_ascii=False)
    new_review_payload = _build_global_review_payload([new_review])[0]
    new_individual_review_json = json.dumps(new_review_payload, ensure_ascii=False)

    logger.info("Previous global review JSON length: %d characters", len(previous_global_review_json))
    logger.info("New individual review JSON length: %d characters", len(new_individual_review_json))

    rendered_prompt = base_prompt.replace(
        "{previous_global_review_json}",
        previous_global_review_json,
    ).replace(
        "{new_individual_review_json}",
        new_individual_review_json,
    )
    logger.info("Rendered incremental global prompt length: %d characters", len(rendered_prompt))

    return _run_global_review_completion(base_prompt, rendered_prompt, request_label="GLOBAL_INCREMENTAL")


def _get_completed_individual_reviews(student, start_date=None, end_date=None):
    qs = IndividualReview.objects.filter(student=student, ai_status=IndividualReview.STATUS_COMPLETED)

    if start_date:
        qs = qs.filter(created_at__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__lte=end_date)

    return qs.order_by("created_at")


def _create_global_review_snapshot(
    *,
    student,
    reviews_qs,
    response_text,
    parsed_response,
    scope_type,
    time_window,
    generation_mode,
    previous_global_review=None,
):
    first_review = reviews_qs.first()
    last_review = reviews_qs.last()
    now = timezone.now()

    global_review = GlobalReview.objects.create(
        student=student,
        scope_type=scope_type,
        time_window=time_window,
        generation_mode=generation_mode,
        previous_global_review=previous_global_review,
        ai_status=GlobalReview.STATUS_COMPLETED,
        ai_raw_response=response_text,
        ai_result=parsed_response,
        based_on_from=first_review.created_at if first_review else None,
        based_on_to=last_review.created_at if last_review else None,
    )

    global_review.individual_reviews.set(reviews_qs)

    qs_without_flag = reviews_qs.filter(has_been_included_in_global_review=False)
    reviews_qs.update(has_been_included_in_global_review=True)
    qs_without_flag.update(first_included_in_global_review_at=now)

    return global_review


def _is_incremental_global_review_usable(global_review):
    if not global_review or not isinstance(global_review.ai_result, dict):
        return False

    required_keys = {
        "summary_text",
        "global_strengths",
        "global_weaknesses",
        "domains",
        "next_session_awareness",
    }
    return required_keys.issubset(global_review.ai_result.keys())


def generate_global_review_for_student(
    student,
    start_date=None,
    end_date=None,
    scope_type=GlobalReview.SCOPE_OVERALL,
    time_window=GlobalReview.WINDOW_CUSTOM,
):
    """
    Generate a GlobalReview snapshot for a given student and optional date range.

    This function can be called from the Django shell or future management commands.
    """
    qs = _get_completed_individual_reviews(student, start_date=start_date, end_date=end_date)

    if not qs.exists():
        return None

    response_text = run_ai_analysis_for_global_review(student, qs)
    if not response_text or not isinstance(response_text, str) or response_text.startswith("Error:"):
        return None

    try:
        parsed = json.loads(response_text)
    except (json.JSONDecodeError, ValueError):
        return None

    return _create_global_review_snapshot(
        student=student,
        reviews_qs=qs,
        response_text=response_text,
        parsed_response=parsed,
        scope_type=scope_type,
        time_window=time_window,
        generation_mode=GlobalReview.GENERATION_FULL_REBUILD,
        previous_global_review=None,
    )

def generate_incremental_global_review_for_student(
    student,
    new_review,
    start_date=None,
    end_date=None,
    scope_type=GlobalReview.SCOPE_OVERALL,
    time_window=GlobalReview.WINDOW_CUSTOM,
):
    """
    Generate a new GlobalReview snapshot by updating the latest existing snapshot
    with one newly completed IndividualReview. Falls back to full rebuild when
    there is no suitable baseline snapshot.
    """
    qs = _get_completed_individual_reviews(student, start_date=start_date, end_date=end_date)

    if not qs.exists() or not qs.filter(id=new_review.id).exists():
        return None

    previous_global_review = (
        GlobalReview.objects.filter(
            student=student,
            scope_type=scope_type,
            time_window=time_window,
        )
        .order_by("-created_at")
        .first()
    )

    if not _is_incremental_global_review_usable(previous_global_review):
        return generate_global_review_for_student(
            student,
            start_date=start_date,
            end_date=end_date,
            scope_type=scope_type,
            time_window=time_window,
        )

    response_text = run_ai_analysis_for_incremental_global_review(
        student,
        previous_global_review,
        new_review,
    )
    if not response_text or not isinstance(response_text, str) or response_text.startswith("Error:"):
        return None

    try:
        parsed = json.loads(response_text)
    except (json.JSONDecodeError, ValueError):
        return None

    return _create_global_review_snapshot(
        student=student,
        reviews_qs=qs,
        response_text=response_text,
        parsed_response=parsed,
        scope_type=scope_type,
        time_window=time_window,
        generation_mode=GlobalReview.GENERATION_INCREMENTAL_UPDATE,
        previous_global_review=previous_global_review,
    )


@login_required
def staff_aura_dashboard(request):
    """
    Staff-only view listing active (flying) students for AURA global review.
    """
    user = request.user
    if getattr(user, "role", None) != "STAFF":
        messages.error(request, "No tiene permisos para acceder a AURA.")
        return redirect("dashboard:dashboard")

    flying_students = (
        StudentProfile.objects.select_related("user")
        .filter(student_phase=StudentProfile.FLYING)
        .order_by("user__last_name", "user__first_name")
    )

    context = {
        "students": flying_students,
    }
    return render(request, "aura/staff_aura_dashboard.html", context)


@login_required
def staff_student_global_review(request, student_profile_id: int):
    """
    Staff-only view to generate and inspect a student's AURA global review.

    For now, this always targets OVERALL + LAST_90_DAYS.
    """
    user = request.user
    if getattr(user, "role", None) != "STAFF":
        messages.error(request, "No tiene permisos para acceder a AURA.")
        return redirect("dashboard:dashboard")

    student_profile = get_object_or_404(
        StudentProfile.objects.select_related("user"),
        id=student_profile_id,
        student_phase=StudentProfile.FLYING,
    )
    student_user = student_profile.user

    # Latest existing global review for default scope/time window
    latest_review = (
        GlobalReview.objects.filter(
            student=student_user,
            scope_type=GlobalReview.SCOPE_OVERALL,
            time_window=GlobalReview.WINDOW_LAST_90_DAYS,
        )
        .order_by("-created_at")
        .first()
    )

    if request.method == "POST":
        # Default: OVERALL + last 90 days
        start_date = timezone.now() - timedelta(days=90)
        new_review = generate_global_review_for_student(
            student_user,
            start_date=start_date,
            end_date=None,
            scope_type=GlobalReview.SCOPE_OVERALL,
            time_window=GlobalReview.WINDOW_LAST_90_DAYS,
        )
        if new_review:
            messages.success(
                request,
                "Se generó el perfil global AURA (últimos 90 días) para este alumno.",
            )
        else:
            messages.error(
                request,
                "No se pudo generar el perfil global AURA. Verifique que existan revisiones individuales.",
            )
        return redirect("aura:staff_student_global_review", student_profile_id=student_profile.id)

    context = {
        "student_profile": student_profile,
        "latest_review": latest_review,
    }
    return render(request, "aura/staff_student_global_review.html", context)
