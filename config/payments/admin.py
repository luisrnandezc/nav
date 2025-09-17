from django.contrib import admin
from django.utils import timezone
from .models import StudentTransaction

@admin.register(StudentTransaction)
class StudentTransactionAdmin(admin.ModelAdmin):
    list_display = ('get_student_username', 'get_student_id', 'amount', 'type', 'date_added',	
                     'get_added_by_username', 'confirmed', 'get_confirmed_by_username', 'get_confirmation_date')
    list_filter = ('confirmed', 'date_added', 'confirmation_date')
    search_fields = ('student_profile__user__username', 'student_profile__user__national_id')
    readonly_fields = ('student_profile', 'amount', 'type', 'date_added', 'added_by', 'confirmed', 'confirmed_by', 'confirmation_date', 'notes')
    
    # Disable add and change functionality
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    fieldsets = (
        ('Información del Estudiante', {
            'fields': ('student_profile',)
        }),
        ('Detalles de la Transacción', {
            'fields': ('amount', 'type', 'category', 'added_by', 'date_added'),
            'description': 'El usuario que agrega la transacción se registra automáticamente.'
        }),
        ('Confirmación de la Transacción', {
            'fields': ('confirmed', 'confirmed_by', 'confirmation_date'),
            'description': 'El usuario que confirma la transacción se registra automáticamente.'
        }),
        ('Notas de la Transacción', {
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
        """Return the username of the user who added the transaction"""
        return obj.added_by.username if obj.added_by else '-'
    get_added_by_username.short_description = 'Agregado por'
    get_added_by_username.admin_order_field = 'added_by__username'

    def get_confirmed_by_username(self, obj):
        """Return the username of the user who confirmed the transaction"""
        return obj.confirmed_by.username if obj.confirmed_by else '-'
    get_confirmed_by_username.short_description = 'Confirmado por'
    get_confirmed_by_username.admin_order_field = 'confirmed_by__username'

    def get_confirmation_date(self, obj):
        """Return only the date part of confirmation_date"""
        return obj.confirmation_date.date() if obj.confirmation_date else '-'
    get_confirmation_date.short_description = 'Fecha de confirmación'
    get_confirmation_date.admin_order_field = 'confirmation_date'

    
    def delete_model(self, request, obj):
        """Override delete_model to ensure balance updates"""
        # Call the model's delete method to trigger balance updates
        obj.delete()
    
    def delete_queryset(self, request, queryset):
        """Override delete_queryset to ensure balance updates"""
        # Call each object's delete method to trigger balance updates
        for obj in queryset:
            obj.delete()