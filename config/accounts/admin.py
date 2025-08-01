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
    list_display = ('get_username', 'get_student_id', 'student_phase', 'get_course_type',
                    'get_course_edition', 'sim_balance', 'flight_balance', 'sim_hours', 'flight_hours')
    list_filter = ('student_phase',)
    search_fields = ('user__username', 'user__national_id', 'user__first_name', 'user__last_name')
    readonly_fields = ('get_course_type', 'get_course_edition')

    def get_username(self, obj):
        return obj.user.username if obj.user else '-'
    get_username.short_description = 'Usuario'
    get_username.admin_order_field = 'user__username'

    def get_student_id(self, obj):
        return obj.user.national_id if obj.user else '-'
    get_student_id.short_description = 'ID'
    get_student_id.admin_order_field = 'user__national_id'

    fieldsets = (
        ('Información del usuario', {
            'fields': ('user',)
        }),
        ('Información del estudiante', {
            'fields': ('student_age', 'student_gender', 'student_phase', 
                       'student_license_type', 'sim_hours', 'flight_hours')
        }),
        ('Información del curso', {
            'fields': ('get_course_type', 'get_course_edition'),
            'description': 'Esta información se actualiza automáticamente según la inscripción del estudiante en los cursos.'
        }),
        ('Balance financiero', {
            'fields': ('sim_balance', 'flight_balance')
        }),
    )

    def get_course_type(self, obj):
        return obj.current_course_type
    get_course_type.short_description = 'Curso'

    def get_course_edition(self, obj):
        return obj.current_course_edition
    get_course_edition.short_description = 'Edición de Curso'

@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'get_instructor_id', 'get_first_name', 'get_last_name',
                     'instructor_license_type', 'instructor_type')
    search_fields = ('user__username', 'user__national_id', 'user__first_name', 'user__last_name')

    def get_username(self, obj):
        return obj.user.username if obj.user else '-'
    get_username.short_description = 'Usuario'
    get_username.admin_order_field = 'user__username'

    def get_instructor_id(self, obj):
        return obj.user.national_id if obj.user else '-'
    get_instructor_id.short_description = 'ID'
    get_instructor_id.admin_order_field = 'user__national_id'

    def get_first_name(self, obj):
        return obj.user.first_name if obj.user else '-'
    get_first_name.short_description = 'Nombre'
    get_first_name.admin_order_field = 'user__first_name'

    def get_last_name(self, obj):
        return obj.user.last_name if obj.user else '-'
    get_last_name.short_description = 'Apellido'
    get_last_name.admin_order_field = 'user__last_name'

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'get_staff_id', 'get_first_name', 'get_last_name')
    search_fields = ('user__username', 'user__national_id', 'user__first_name', 'user__last_name')

    def get_username(self, obj):
        return obj.user.username if obj.user else '-'
    get_username.short_description = 'Usuario'
    get_username.admin_order_field = 'user__username'

    def get_staff_id(self, obj):
        return obj.user.national_id if obj.user else '-'
    get_staff_id.short_description = 'ID'
    get_staff_id.admin_order_field = 'user__national_id'

    def get_first_name(self, obj):
        return obj.user.first_name if obj.user else '-'
    get_first_name.short_description = 'Nombre'
    get_first_name.admin_order_field = 'user__first_name'

    def get_last_name(self, obj):
        return obj.user.last_name if obj.user else '-'
    get_last_name.short_description = 'Apellido'
    get_last_name.admin_order_field = 'user__last_name'

admin.site.register(User, CustomUserAdmin)