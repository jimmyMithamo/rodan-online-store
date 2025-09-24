from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Order, OrderItem, Coupon, CouponUsage
from payments.models import Payment
from core.models import AuditLog


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['product', 'product_variation', 'quantity', 'unit_price', 'subtotal']
    readonly_fields = ['subtotal']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ['payment_method', 'payment_reference', 'amount', 'status', 'paid_at']
    readonly_fields = ['payment_reference', 'paid_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'status', 'payment_method', 'total_amount',
        'created_at', 'order_items_count', 'payment_status'
    ]
    list_filter = [
        'status', 'payment_method', 'created_at', 'shipping_country'
    ]
    search_fields = [
        'order_number', 'user__email', 'user__first_name', 'user__last_name',
        'shipping_first_name', 'shipping_last_name', 'shipping_email'
    ]
    readonly_fields = [
        'order_number', 'subtotal', 'total_amount', 'created_at', 'updated_at',
        'full_shipping_address'
    ]
    inlines = [OrderItemInline, PaymentInline]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_method', 'created_at', 'updated_at')
        }),
        ('Shipping Address', {
            'fields': (
                'shipping_first_name', 'shipping_last_name', 'shipping_email', 'shipping_phone',
                'shipping_address_line_1', 'shipping_address_line_2', 'shipping_city',
                'shipping_postal_code', 'shipping_country', 'full_shipping_address'
            )
        }),
        ('Order Totals', {
            'fields': ('subtotal', 'shipping_cost', 'tax_amount', 'discount_amount', 'total_amount')
        }),
        ('Coupon & Discount', {
            'fields': ('coupon', 'coupon_code'),
            'classes': ('collapse',)
        }),
        ('Tracking & Notes', {
            'fields': ('tracking_number', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('confirmed_at', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        })
    )

    def order_items_count(self, obj):
        """Display number of items in order"""
        return obj.items.count()
    order_items_count.short_description = 'Items'

    def payment_status(self, obj):
        """Display payment status with color coding"""
        latest_payment = obj.payments.first()
        if not latest_payment:
            return format_html('<span style="color: gray;">No Payment</span>')
        
        color_map = {
            'completed': 'green',
            'pending': 'orange',
            'failed': 'red',
            'cancelled': 'red',
            'refunded': 'blue'
        }
        color = color_map.get(latest_payment.status, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            latest_payment.get_status_display()
        )
    payment_status.short_description = 'Payment Status'

    def save_model(self, request, obj, form, change):
        """Update timestamps based on status changes"""
        if change:
            if obj.status == 'confirmed' and not obj.confirmed_at:
                obj.confirmed_at = timezone.now()
            elif obj.status == 'shipped' and not obj.shipped_at:
                obj.shipped_at = timezone.now()
            elif obj.status == 'delivered' and not obj.delivered_at:
                obj.delivered_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'order', 'product_name', 'product_sku', 'quantity', 'unit_price', 'subtotal'
    ]
    list_filter = ['order__status', 'created_at']
    search_fields = [
        'order__order_number', 'product__name', 'product_name', 'product_sku'
    ]
    readonly_fields = ['subtotal', 'product_name', 'product_sku', 'variation_details']
    ordering = ['-created_at']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'discount_type', 'discount_value', 'times_used', 'usage_limit',
        'is_active', 'is_currently_valid', 'start_date', 'end_date'
    ]
    list_filter = [
        'discount_type', 'is_active', 'start_date', 'end_date', 'created_at'
    ]
    search_fields = ['code', 'description']
    filter_horizontal = ['applicable_products', 'applicable_categories']
    readonly_fields = ['times_used', 'created_at', 'updated_at', 'is_currently_valid']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'description', 'is_active')
        }),
        ('Discount Configuration', {
            'fields': ('discount_type', 'discount_value', 'minimum_order_amount')
        }),
        ('Usage Limits', {
            'fields': ('usage_limit', 'usage_limit_per_user', 'times_used')
        }),
        ('Validity Period', {
            'fields': ('start_date', 'end_date', 'is_currently_valid')
        }),
        ('Applicable Items', {
            'fields': ('applicable_products', 'applicable_categories'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def is_currently_valid(self, obj):
        """Display if coupon is currently valid"""
        return obj.is_valid
    is_currently_valid.boolean = True
    is_currently_valid.short_description = 'Currently Valid'


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'user', 'order', 'used_at']
    list_filter = ['coupon', 'used_at']
    search_fields = ['coupon__code', 'user__email', 'order__order_number']
    readonly_fields = ['used_at']
    ordering = ['-used_at']
