# Admin customization
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, InstructorProfile, StaffProfile, StudentPayment

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

@admin.register(StudentPayment)
class StudentPaymentAdmin(admin.ModelAdmin):
    list_display = ('student_profile', 'amount', 'date_added', 'confirmed', 'confirmation_date')
    list_filter = ('confirmed', 'date_added')
    search_fields = (
        'student_profile__user__username',
        'student_profile__user__first_name',
        'student_profile__user__last_name',
        'student_profile__user__national_id'
    )
    readonly_fields = ('date_added', 'confirmation_date')
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student_profile',)
        }),
        ('Payment Information', {
            'fields': ('amount', 'date_added', 'notes')
        }),
        ('Confirmation Information', {
            'fields': ('confirmed', 'confirmed_by', 'confirmation_date'),
            'description': 'Solo el personal autorizado puede confirmar pagos.'
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not hasattr(request.user, 'staff_profile') or not request.user.staff_profile.can_confirm_payments:
            readonly_fields.extend(['confirmed', 'confirmed_by'])
        return readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:  # Only set added_by on creation
            obj.added_by = request.user
        super().save_model(request, obj, form, change)

admin.site.register(User, CustomUserAdmin)
admin.site.register(InstructorProfile)
admin.site.register(StaffProfile)