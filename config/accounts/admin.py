# Admin customization
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, InstructorProfile, StaffProfile

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'first_name', 'last_name', 'national_id', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'first_name', 'last_name', 'national_id', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'national_id', 'role', 'password1', 'password2')
        }),
    )
    search_fields = ('username', 'email', 'national_id', 'first_name', 'last_name')
    ordering = ('username',)

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_phase', 'get_course_type', 'get_course_edition')
    list_filter = ('student_phase',)
    search_fields = ('user__username', 'user__national_id', 'user__first_name', 'user__last_name')
    readonly_fields = ('get_course_type', 'get_course_edition')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Student Information', {
            'fields': ('student_age', 'student_gender', 'student_phase', 'student_license_type')
        }),
        ('Course Information', {
            'fields': ('get_course_type', 'get_course_edition'),
            'description': 'Esta información se actualiza automáticamente según la inscripción del estudiante en los cursos.'
        }),
        ('Balance Information', {
            'fields': ('student_balance',)
        }),
    )

    def get_course_type(self, obj):
        return obj.current_course_type
    get_course_type.short_description = 'Curso'

    def get_course_edition(self, obj):
        return obj.current_course_edition
    get_course_edition.short_description = 'Edición de Curso'

admin.site.register(User, CustomUserAdmin)
admin.site.register(InstructorProfile)
admin.site.register(StaffProfile)