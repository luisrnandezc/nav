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
    list_display = ('get_student_name', 'get_student_id', 'grade', 'test_type', 'get_subject_info', 'get_instructor_name', 'date')
    list_filter = ('subject_edition__subject_type__course_type', 'subject_edition__time_slot', 'test_type', 'date')
    search_fields = ('student__first_name', 'student__last_name', 'student__national_id', 'subject_edition__subject_type__name', 'subject_edition__subject_type__code', 'instructor__first_name', 'instructor__last_name', 'instructor__national_id')
    readonly_fields = ('student', 'instructor', 'date', 'student_national_id', 'student_first_name', 'student_last_name', 'instructor_national_id', 'instructor_first_name', 'instructor_last_name', 'subject_name')
    list_select_related = ('student', 'instructor', 'subject_edition', 'subject_edition__subject_type')
    
    fieldsets = (
        ('Información del estudiante', {
            'fields': ('student', 'student_national_id', 'student_first_name', 'student_last_name'),
        }),
        ('Información del instructor', {
            'fields': ('instructor', 'instructor_national_id', 'instructor_first_name', 'instructor_last_name'),
        }),
        ('Calificación', {
            'fields': ('subject_edition', 'subject_name', 'grade', 'test_type', 'date'),
        }),
    )

    def has_add_permission(self, request):
        return False  # Disable adding new grades from admin

    def student_national_id(self, obj):
        return obj.student.national_id if obj.student else '-'
    student_national_id.short_description = 'ID'

    def student_first_name(self, obj):
        return obj.student.first_name if obj.student else '-'
    student_first_name.short_description = 'Nombre'

    def student_last_name(self, obj):
        return obj.student.last_name if obj.student else '-'
    student_last_name.short_description = 'Apellido'

    def instructor_national_id(self, obj):
        return obj.instructor.national_id if obj.instructor else '-'
    instructor_national_id.short_description = 'ID'

    def instructor_first_name(self, obj):
        return obj.instructor.first_name if obj.instructor else '-'
    instructor_first_name.short_description = 'Nombre'

    def instructor_last_name(self, obj):
        return obj.instructor.last_name if obj.instructor else '-'
    instructor_last_name.short_description = 'Apellido'

    def subject_name(self, obj):
        if obj.subject_edition and obj.subject_edition.subject_type:
            # Get the human-readable name from the choices tuple
            from .models import SUBJECTS_NAMES
            subject_code = obj.subject_edition.subject_type.code
            # Find the matching tuple and return the second value (human-readable name)
            for code, name in SUBJECTS_NAMES:
                if code == subject_code:
                    return name
            return subject_code  # Fallback to code if not found in choices
        return '-'
    subject_name.short_description = 'Nombre de la Materia'

    def get_subject_info(self, obj):
        if obj.subject_edition and obj.subject_edition.subject_type:
            return f"{obj.subject_edition.subject_type.code} ({obj.subject_edition.time_slot})"
        return '-'
    get_subject_info.short_description = 'Materia'
    get_subject_info.admin_order_field = 'subject_edition__subject_type__code'

    def get_student_name(self, obj):
        if obj.student:
            return f"{obj.student.first_name} {obj.student.last_name}"
        return '-'
    get_student_name.short_description = 'Estudiante'
    get_student_name.admin_order_field = 'student__first_name'

    def get_student_id(self, obj):
        if obj.student:
            return obj.student.national_id
        return '-'
    get_student_id.short_description = 'ID Estudiante'
    get_student_id.admin_order_field = 'student__national_id'

    def get_instructor_name(self, obj):
        if obj.instructor:
            return f"{obj.instructor.first_name} {obj.instructor.last_name}"
        return '-'
    get_instructor_name.short_description = 'Instructor'
    get_instructor_name.admin_order_field = 'instructor__first_name'
