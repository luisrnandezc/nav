from django.contrib import admin
from .models import StudentPayment
from django.utils import timezone

@admin.register(StudentPayment)
class StudentPaymentAdmin(admin.ModelAdmin):
    list_display = ('get_student_username', 'get_student_id', 'amount', 'get_date_added',
                     'get_added_by_username', 'confirmed', 'get_confirmed_by_username', 'get_confirmation_date')
    list_filter = ('confirmed', 'date_added', 'confirmation_date')
    search_fields = ('student_profile__user__username', 'student_profile__user__national_id')
    readonly_fields = ('date_added', 'added_by', 'confirmation_date', 'confirmed_by')
    fieldsets = (
        ('Información del Estudiante', {
            'fields': ('student_profile',)
        }),
        ('Detalles del Pago', {
            'fields': ('amount', 'type', 'added_by', 'date_added'),
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
    get_student_username.short_description = 'Usuario'
    get_student_username.admin_order_field = 'student_profile__user__username'

    def get_student_id(self, obj):
        return obj.student_profile.user.national_id if obj.student_profile else '-'
    get_student_id.short_description = 'ID'
    get_student_id.admin_order_field = 'student_profile__user__national_id'

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
        
        # Make amount and type readonly for existing payments
        if obj and obj.pk:  # If this is an existing payment
            readonly_fields.extend(['student_profile', 'amount', 'type'])
        
        # Make confirmed field readonly for users without confirmation permissions
        if not hasattr(request.user, 'staff_profile') or not request.user.staff_profile.can_confirm_payments:
            readonly_fields.extend(['confirmed'])
        
        return readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:  # New payment
            obj.added_by = request.user
            if obj.confirmed:  # If payment is confirmed on creation
                obj.confirm(request.user)
            else:
                super().save_model(request, obj, form, change)
        elif change:  # Existing payment being modified
            # Get the original object to check if it was previously confirmed
            original_obj = StudentPayment.objects.get(pk=obj.pk)
            
            if obj.confirmed and not original_obj.confirmed:  # Payment being confirmed
                obj.confirm(request.user)
            elif not obj.confirmed and original_obj.confirmed:  # Payment being unconfirmed
                obj.unconfirm()
                # The unconfirm method already saves the object, so we don't need to call super().save_model()
            else:
                super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Override delete_model to handle balance updates when deleting confirmed payments"""
        if obj.confirmed:
            obj._update_student_balance(add=False)
        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        """Override delete_queryset to handle balance updates when bulk deleting confirmed payments"""
        for payment in queryset:
            if payment.confirmed:
                payment._update_student_balance(add=False)
        super().delete_queryset(request, queryset)