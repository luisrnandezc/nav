from django.contrib import admin
from academic.models import CourseType, CourseEdition, SubjectType, SubjectEdition


@admin.register(CourseType)
class CourseTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')
    ordering = ('code',)

@admin.register(CourseEdition)
class CourseEditionAdmin(admin.ModelAdmin):
    list_display = ('course_type', 'edition', 'start_date', 'time_slot', 'get_students_count')
    list_filter = ('course_type', 'time_slot', 'start_date')
    search_fields = ('course_type__name', 'course_type__code')
    ordering = ('-start_date', 'course_type')
    filter_horizontal = ('students',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "course_type":
            kwargs["initial"] = CourseType.objects.filter(code='PPA').first()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_students_count(self, obj):
        return obj.students.count()
    get_students_count.short_description = 'Estudiantes'

@admin.register(SubjectType)
class SubjectTypeAdmin(admin.ModelAdmin):
    fields = ['course_type', 'code', 'name', 'credit_hours', 'passing_grade', 'recovery_passing_grade']
    list_display = ('code', 'name', 'course_type', 'credit_hours', 'passing_grade', 'recovery_passing_grade')
    list_filter = ('course_type',)
    search_fields = ('code', 'name', 'course_type__name')
    ordering = ('course_type', 'code')

@admin.register(SubjectEdition)
class SubjectEditionAdmin(admin.ModelAdmin):
    list_display = ('subject_type', 'instructor', 'time_slot', 'start_date', 'end_date', 'get_students_count')
    list_filter = ('subject_type__course_type', 'time_slot', 'start_date')
    search_fields = ('subject_type__name', 'subject_type__code', 'instructor__user__username')
    ordering = ('-start_date', 'subject_type')
    filter_horizontal = ('students',)

    def get_students_count(self, obj):
        return obj.students.count()
    get_students_count.short_description = 'Estudiantes'
