from django.contrib import admin

from .models import IndividualReview, GlobalReview


@admin.register(IndividualReview)
class IndividualReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "instructor",
        "ai_status",
        "has_been_included_in_global_review",
        "created_at",
    )
    list_filter = (
        "ai_status",
        "has_been_included_in_global_review",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "id",
        "student__first_name",
        "student__last_name",
        "student__email",
        "instructor__first_name",
        "instructor__last_name",
        "instructor__email",
        "source_comment_text",
    )
    date_hierarchy = "created_at"
    readonly_fields = (
        "created_at",
        "updated_at",
        "first_included_in_global_review_at",
    )


@admin.register(GlobalReview)
class GlobalReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "scope_type",
        "time_window",
        "ai_status",
        "created_at",
    )
    list_filter = (
        "scope_type",
        "time_window",
        "ai_status",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "id",
        "student__first_name",
        "student__last_name",
        "student__email",
    )
    filter_horizontal = ("individual_reviews",)
    date_hierarchy = "created_at"
    readonly_fields = (
        "created_at",
        "updated_at",
        "based_on_from",
        "based_on_to",
    )

