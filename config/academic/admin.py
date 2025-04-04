from django.contrib import admin
from .models import CourseType, CourseEdition, SubjectType, SubjectEdition

@admin.register(CourseType)
class CourseTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'credit_hours')
    search_fields = ('code', 'name')
    ordering = ('code',)

@admin.register(CourseEdition)
class CourseEditionAdmin(admin.ModelAdmin):
    list_display = ('course_type', 'edition', 'start_date', 'time_slot')
    list_filter = ('course_type', 'time_slot')
    search_fields = ('course_type__name', 'course_type__code')
    filter_horizontal = ('students',)

@admin.register(SubjectType)
class SubjectTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'course_type', 'credit_hours', 'passing_grade')
    list_filter = ('course_type',)
    search_fields = ('code', 'name', 'course_type__name')

@admin.register(SubjectEdition)
class SubjectEditionAdmin(admin.ModelAdmin):
    list_display = ('subject_type', 'instructor', 'time_slot', 'start_date', 'end_date')
    list_filter = ('subject_type__course_type', 'time_slot')
    search_fields = ('subject_type__name', 'subject_type__code', 'instructor__username')
    filter_horizontal = ('students',)
