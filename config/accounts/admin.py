from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Student, Instructor, Staff

# ------------------------------
# Custom Inline for Student Data
# ------------------------------
class StudentInline(admin.StackedInline):
    model = Student
    can_delete = False
    verbose_name_plural = 'Student'
    fk_name = 'user'
    extra = 0  # No extra blank forms
    fieldsets = (
        ('Información Personal', {
            'fields': ('student_id', 'student_age', 'student_gender')
        }),
        ('Información Académica', {
            'fields': ('student_phase', 'student_course_type',
                       'student_course_number', 'student_license_type',
                       'student_balance',
            )
        })
    )
    readonly_fields = ('student_course_type', 'student_course_number')

# ------------------------------
# Custom Inline for Instructor Data
# ------------------------------
class InstructorInline(admin.StackedInline):
    model = Instructor
    can_delete = False
    verbose_name_plural = 'Instructor'
    fk_name = 'user'
    extra = 0  # No extra blank forms
    fieldsets = (
        ('Información Personal', {
            'fields': ('instructor_id',)
        }),
        ('Información Académica', {
            'fields': ('instructor_type', 'instructor_license_type')
        })
    )

# ------------------------------
# Custom Inline for Staff Data
# ------------------------------
class StaffInline(admin.StackedInline):
    model = Staff
    can_delete = False
    verbose_name_plural = 'Staff'
    fk_name = 'user'
    extra = 0  # No extra blank forms
    fieldsets = (
        ('Información Personal', {
            'fields': ('staff_id',)
        }),
    )

# ------------------------------
# Custom UserAdmin
# ------------------------------
class CustomUserAdmin(BaseUserAdmin):
    inlines = (StudentInline, InstructorInline, StaffInline)

    fieldsets = (
        ('Login Info', {
            'fields': ('username', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
        ('Custom Fields', {
            'fields': ()  # Placeholder to add User-specific fields
        }),
    )

    list_display = BaseUserAdmin.list_display + ('email',)


# Unregister the default User admin and register the custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
