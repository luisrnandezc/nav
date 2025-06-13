from django.contrib import admin
from .models import CourseType, CourseEdition, SubjectType, SubjectEdition, StudentGrade
from accounts.models import User

@admin.register(CourseType)
class CourseTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'credit_hours')
    search_fields = ('code', 'name')
    ordering = ('code',)

@admin.register(CourseEdition)
class CourseEditionAdmin(admin.ModelAdmin):
    list_display = ('get_course_code', 'course_type', 'edition', 'start_date', 'time_slot')
    list_filter = ('course_type', 'time_slot')
    search_fields = ('course_type__name', 'course_type__code')
    filter_horizontal = ('students',)

    def get_course_code(self, obj):
        return obj.course_type.code if obj.course_type else '-'
    get_course_code.short_description = 'Código'
    get_course_code.admin_order_field = 'course_type__code'

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
    list_display = ('student_username', 'get_student_id', 'grade', 'test_type', 'get_subject_info', 'submitted_by_username', 'date')
    list_filter = ('subject_edition__subject_type__course_type', 'subject_edition__time_slot', 'test_type', 'date')
    search_fields = ('student_username', 'subject_edition__subject_type__name', 'subject_edition__subject_type__code', 'submitted_by_username', 'student__first_name', 'student__last_name')
    readonly_fields = ('submitted_by_username', 'date')

    def has_add_permission(self, request):
        return False  # Disable adding new grades from admin

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "student":
            kwargs["queryset"] = User.objects.filter(role='STUDENT').order_by('first_name', 'last_name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_subject_info(self, obj):
        if obj.subject_edition and obj.subject_edition.subject_type:
            return f"{obj.subject_edition.subject_type.code} ({obj.subject_edition.time_slot})"
        return '-'
    get_subject_info.short_description = 'Materia'
    get_subject_info.admin_order_field = 'subject_edition__subject_type__code'

    def get_student_id(self, obj):
        return obj.student.national_id if obj.student else '-'
    get_student_id.short_description = 'ID'
    get_student_id.admin_order_field = 'student__national_id'
