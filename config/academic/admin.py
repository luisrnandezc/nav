from django.contrib import admin
from .models import CourseType, CourseEdition, SubjectType, SubjectEdition, StudentGrade

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
    list_display = ('get_subject_code', 'instructor', 'time_slot', 'start_date', 'end_date')
    list_filter = ('subject_type__course_type', 'time_slot')
    search_fields = ('subject_type__name', 'subject_type__code', 'instructor__username')
    filter_horizontal = ('students',)

    def get_subject_code(self, obj):
        return obj.subject_type.code if obj.subject_type else '-'
    get_subject_code.short_description = 'Materia'
    get_subject_code.admin_order_field = 'subject_type__code'

@admin.register(StudentGrade)
class StudentGradeAdmin(admin.ModelAdmin):
    list_display = ('get_subject_info', 'get_student_username', 'grade', 'test_type')
    list_filter = ('subject_edition__subject_type__course_type', 'test_type')
    search_fields = ('subject_edition__subject_type__name', 'subject_edition__subject_type__code', 'student__username')

    def get_subject_info(self, obj):
        if obj.subject_edition and obj.subject_edition.subject_type:
            return f"{obj.subject_edition.subject_type.code} ({obj.subject_edition.time_slot})"
        return '-'
    get_subject_info.short_description = 'Materia'
    get_subject_info.admin_order_field = 'subject_edition__subject_type__code'

    def get_student_username(self, obj):
        return obj.student.username if obj.student else '-'
    get_student_username.short_description = 'Estudiante'
    get_student_username.admin_order_field = 'student__username'
