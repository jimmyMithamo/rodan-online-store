from django.contrib import admin
from django.utils.html import format_html
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_reference', 'order_number', 'user_email', 'amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['payment_reference', 'order__order_number', 'user__email', 'transaction_id']
    readonly_fields = ['payment_reference', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_reference', 'order', 'user', 'amount', 'payment_method')
        }),
        ('Status', {
            'fields': ('status', 'transaction_id', 'paid_at')
        }),
        ('Gateway Response', {
            'fields': ('gateway_response',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = 'Order Number'
    order_number.admin_order_field = 'order__order_number'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def colored_status(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray',
            'refunded': 'purple'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    colored_status.short_description = 'Status'
    colored_status.admin_order_field = 'status'
