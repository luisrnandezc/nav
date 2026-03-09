import json
import logging
import os
import sys

from django.conf import settings
from openai import OpenAI


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
