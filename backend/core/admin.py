from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'action', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__email', 'action', 'ip_address']
    readonly_fields = ['user', 'ip_address', 'action', 'details', 'timestamp']
    ordering = ['-timestamp']
    
    def user_email(self, obj):
        return obj.user.email if obj.user else 'Anonymous'
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def has_add_permission(self, request):
        # Audit logs should not be manually created
        return False
    
    def has_change_permission(self, request, obj=None):
        # Audit logs should not be edited
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete audit logs
        return request.user.is_superuser
