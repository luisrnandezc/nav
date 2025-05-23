# Admin customization
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, InstructorProfile, StaffProfile, StudentPayment
from django.utils import timezone

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
    list_display = ('user', 'student_phase', 'get_course_type', 'get_course_edition', 'get_student_balance')
    list_filter = ('student_phase',)
    search_fields = ('user__username', 'user__national_id', 'user__first_name', 'user__last_name')
    readonly_fields = ('get_course_type', 'get_course_edition', 'get_student_balance')
    
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
            'fields': ('get_student_balance',)
        }),
    )

    def get_course_type(self, obj):
        return obj.current_course_type
    get_course_type.short_description = 'Curso'

    def get_course_edition(self, obj):
        return obj.current_course_edition
    get_course_edition.short_description = 'Edición de Curso'

    def get_student_balance(self, obj):
        return obj.student_balance
    get_student_balance.short_description = 'Balance de vuelo'

@admin.register(StudentPayment)
class StudentPaymentAdmin(admin.ModelAdmin):
    list_display = ('get_student_full_name', 'amount', 'date_added', 'added_by', 'confirmed', 'confirmed_by', 'confirmation_date')
    list_filter = ('confirmed', 'date_added', 'confirmation_date')
    search_fields = ('student_profile__user__first_name', 'student_profile__user__last_name', 'student_profile__user__national_id')
    readonly_fields = ( 'date_added', 'added_by', 'confirmation_date', 'confirmed_by')
    fieldsets = (
        ('Información del Estudiante', {
            'fields': ('student_profile',)
        }),
        ('Detalles del Pago', {
            'fields': ('amount', 'date_added'),
            'description': 'El usuario que agrega el pago se registrará automáticamente.'
        }),
        ('Confirmación', {
            'fields': ('confirmed', 'confirmation_date'),
            'description': 'Al confirmar el pago, se registrará automáticamente su usuario como confirmador.'
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not hasattr(request.user, 'staff_profile') or not request.user.staff_profile.can_confirm_payments:
            readonly_fields.extend(['confirmed'])
        return readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:  # New payment
            obj.added_by = request.user
            if obj.confirmed:  # If payment is confirmed on creation
                obj.confirmed_by = request.user
                obj.confirmation_date = timezone.now()
        elif obj.confirmed and not obj.confirmed_by:  # Existing payment being confirmed
            obj.confirmed_by = request.user
            obj.confirmation_date = timezone.now()
        super().save_model(request, obj, form, change)

admin.site.register(User, CustomUserAdmin)
admin.site.register(InstructorProfile)
admin.site.register(StaffProfile)