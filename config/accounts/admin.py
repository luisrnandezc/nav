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
    list_display = ('get_student_username', 'amount', 'get_date_added', 'get_added_by_username', 'confirmed', 'get_confirmed_by_username', 'get_confirmation_date')
    list_filter = ('confirmed', 'date_added', 'confirmation_date')
    search_fields = ('student_profile__user__username', 'student_profile__user__national_id')
    readonly_fields = ('date_added', 'added_by', 'confirmation_date', 'confirmed_by')
    fieldsets = (
        ('Información del Estudiante', {
            'fields': ('student_profile',)
        }),
        ('Detalles del Pago', {
            'fields': ('amount', 'added_by', 'date_added'),
            'description': 'El usuario que agrega el pago se registra automáticamente.'
        }),
        ('Confirmación', {
            'fields': ('confirmed', 'confirmed_by', 'confirmation_date'),
            'description': 'El usuario que confirma el pago se registra automáticamente.'
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
    )

    def get_student_username(self, obj):
        """Return the student's username for admin display"""
        return obj.student_profile.user.username
    get_student_username.short_description = 'Estudiante'
    get_student_username.admin_order_field = 'student_profile__user__username'

    def get_added_by_username(self, obj):
        """Return the username of the user who added the payment"""
        return obj.added_by.username if obj.added_by else '-'
    get_added_by_username.short_description = 'Agregado por'
    get_added_by_username.admin_order_field = 'added_by__username'

    def get_confirmed_by_username(self, obj):
        """Return the username of the user who confirmed the payment"""
        return obj.confirmed_by.username if obj.confirmed_by else '-'
    get_confirmed_by_username.short_description = 'Confirmado por'
    get_confirmed_by_username.admin_order_field = 'confirmed_by__username'

    def get_date_added(self, obj):
        """Return only the date part of date_added"""
        return obj.date_added.date()
    get_date_added.short_description = 'Fecha de pago'
    get_date_added.admin_order_field = 'date_added'

    def get_confirmation_date(self, obj):
        """Return only the date part of confirmation_date"""
        return obj.confirmation_date.date() if obj.confirmation_date else '-'
    get_confirmation_date.short_description = 'Fecha de confirmación'
    get_confirmation_date.admin_order_field = 'confirmation_date'

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