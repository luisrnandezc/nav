from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class IndividualReview(models.Model):
    """
    Atomic AI analysis of training feedback for a student.

    Typically represents the AI analysis of one instructor comment or
    one session's debrief, tied to a student and optional session context.
    """

    STATUS_PENDING = "PENDING"
    STATUS_PROCESSING = "PROCESSING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_FAILED = "FAILED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="aura_individual_reviews_as_student",
    )

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="aura_individual_reviews_as_instructor",
        blank=True,
        null=True,
    )

    # Optional generic relation to a sim/flight/session model
    session_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    session_object_id = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    session = GenericForeignKey("session_content_type", "session_object_id")

    # Raw instructor comment(s) or debrief text that AURA will analyze
    source_comment_text = models.TextField()

    # AI lifecycle and results
    ai_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )

    ai_raw_response = models.TextField(
        blank=True,
        null=True,
        help_text="Optional raw response text returned by the AI model (for debugging).",
    )

    ai_result = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Structured JSON result for this individual review (tags, mini-summary, etc.).",
    )

    # Aggregation bookkeeping
    has_been_included_in_global_review = models.BooleanField(
        default=False,
        help_text="Indicates whether this review has ever been used to build a global review.",
    )

    first_included_in_global_review_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp when this review was first included in any global review.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Individual review"
        verbose_name_plural = "Individual reviews"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"IndividualReview #{self.id} for {self.student} (status={self.ai_status})"


class GlobalReview(models.Model):
    """
    Aggregated AI profile for a student over many IndividualReview instances.

    Designed to be flexible regarding scope (sim, flight, course, overall)
    and time window (all time, recent N days, etc.).
    """

    # Scope of what this global review represents
    SCOPE_OVERALL = "OVERALL"
    SCOPE_SIM_ONLY = "SIM_ONLY"
    SCOPE_FLIGHT_ONLY = "FLIGHT_ONLY"
    SCOPE_COURSE = "COURSE"
    SCOPE_CUSTOM = "CUSTOM"

    SCOPE_CHOICES = [
        (SCOPE_OVERALL, "Overall training profile"),
        (SCOPE_SIM_ONLY, "Simulator sessions only"),
        (SCOPE_FLIGHT_ONLY, "Flight sessions only"),
        (SCOPE_COURSE, "Specific course/module"),
        (SCOPE_CUSTOM, "Custom scope"),
    ]

    # How the time range of IndividualReviews was chosen
    WINDOW_ALL_TIME = "ALL_TIME"
    WINDOW_LAST_90_DAYS = "LAST_90_DAYS"
    WINDOW_LAST_20_SESSIONS = "LAST_20_SESSIONS"
    WINDOW_CUSTOM = "CUSTOM"

    WINDOW_CHOICES = [
        (WINDOW_ALL_TIME, "All time"),
        (WINDOW_LAST_90_DAYS, "Last 90 days"),
        (WINDOW_LAST_20_SESSIONS, "Last 20 sessions"),
        (WINDOW_CUSTOM, "Custom window"),
    ]

    # Reuse the same AI lifecycle choices as IndividualReview
    STATUS_PENDING = IndividualReview.STATUS_PENDING
    STATUS_PROCESSING = IndividualReview.STATUS_PROCESSING
    STATUS_COMPLETED = IndividualReview.STATUS_COMPLETED
    STATUS_FAILED = IndividualReview.STATUS_FAILED

    STATUS_CHOICES = IndividualReview.STATUS_CHOICES

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="aura_global_reviews",
    )

    scope_type = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default=SCOPE_OVERALL,
        help_text="Logical scope of this global review (overall, sim-only, flight-only, etc.).",
    )

    time_window = models.CharField(
        max_length=20,
        choices=WINDOW_CHOICES,
        default=WINDOW_ALL_TIME,
        help_text="How the date/session range was selected when generating this review.",
    )

    # Optional M2M link to the individual reviews used to build this snapshot
    individual_reviews = models.ManyToManyField(
        IndividualReview,
        related_name="global_reviews",
        blank=True,
        help_text="Individual reviews that were aggregated to build this profile.",
    )

    # AI lifecycle and results
    ai_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )

    ai_result = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text=(
            "Structured JSON profile (strengths, weaknesses, recommendations, "
            "summary text, etc.) produced by the AI."
        ),
    )

    ai_raw_response = models.TextField(
        blank=True,
        null=True,
        help_text="Optional raw response text returned by the AI model (for debugging).",
    )

    # Metadata about what was considered for this snapshot
    based_on_from = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Earliest created_at of IndividualReviews considered for this global review.",
    )

    based_on_to = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Latest created_at of IndividualReviews considered for this global review.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Global review"
        verbose_name_plural = "Global reviews"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"GlobalReview #{self.id} for {self.student} ({self.scope_type}, {self.time_window})"

