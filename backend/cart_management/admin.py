from django.contrib import admin
from django.utils.html import format_html
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    """Inline admin for cart items"""
    model = CartItem
    extra = 0
    fields = ['product', 'product_variation', 'quantity', 'unit_price', 'subtotal', 'is_available']
    readonly_fields = ['unit_price', 'subtotal', 'is_available']

    def unit_price(self, obj):
        """Display unit price"""
        return f"${obj.unit_price:.2f}"
    unit_price.short_description = 'Unit Price'

    def subtotal(self, obj):
        """Display subtotal"""
        return f"${obj.subtotal:.2f}"
    subtotal.short_description = 'Subtotal'

    def is_available(self, obj):
        """Display availability status"""
        if obj.is_available:
            return format_html('<span style="color: green;">✓ Available</span>')
        else:
            return format_html('<span style="color: red;">✗ Unavailable</span>')
    is_available.short_description = 'Availability'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin for Cart model"""
    list_display = ['user', 'total_items', 'unique_items_count', 'cart_total', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['total_items', 'unique_items_count', 'cart_total', 'created_at', 'updated_at']
    inlines = [CartItemInline]

    fieldsets = (
        ('Cart Information', {
            'fields': ('user', 'created_at', 'updated_at')
        }),
        ('Cart Summary', {
            'fields': ('total_items', 'unique_items_count', 'cart_total'),
            'classes': ('collapse',)
        })
    )

    def total_items(self, obj):
        """Display total items count"""
        return obj.total_items
    total_items.short_description = 'Total Items'

    def unique_items_count(self, obj):
        """Display unique items count"""
        return obj.unique_items_count
    unique_items_count.short_description = 'Unique Items'

    def cart_total(self, obj):
        """Display cart total"""
        return f"${obj.cart_total:.2f}"
    cart_total.short_description = 'Cart Total'

    def has_delete_permission(self, request, obj=None):
        """Allow deletion of carts"""
        return True

    def get_queryset(self, request):
        """Optimize queryset with prefetch_related"""
        return super().get_queryset(request).select_related('user').prefetch_related('items')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Admin for CartItem model"""
    list_display = ['cart_user', 'product_name', 'product_sku', 'quantity', 'unit_price_display', 'subtotal_display', 'availability_status', 'updated_at']
    list_filter = ['created_at', 'updated_at', 'product__category']
    search_fields = ['cart__user__email', 'product__name', 'product__sku', 'product_variation__sku']
    readonly_fields = ['unit_price_display', 'subtotal_display', 'product_name', 'product_sku', 'variation_details', 'availability_status']
    
    fieldsets = (
        ('Cart Item Information', {
            'fields': ('cart', 'product', 'product_variation', 'quantity')
        }),
        ('Product Details', {
            'fields': ('product_name', 'product_sku', 'variation_details'),
            'classes': ('collapse',)
        }),
        ('Pricing', {
            'fields': ('unit_price_display', 'subtotal_display'),
            'classes': ('collapse',)
        }),
        ('Availability', {
            'fields': ('availability_status',),
            'classes': ('collapse',)
        })
    )

    def cart_user(self, obj):
        """Display cart user"""
        return obj.cart.user.email
    cart_user.short_description = 'User'
    cart_user.admin_order_field = 'cart__user__email'

    def product_name(self, obj):
        """Display product name"""
        return obj.product_name
    product_name.short_description = 'Product'

    def product_sku(self, obj):
        """Display product SKU"""
        return obj.product_sku
    product_sku.short_description = 'SKU'

    def unit_price_display(self, obj):
        """Display unit price"""
        return f"${obj.unit_price:.2f}"
    unit_price_display.short_description = 'Unit Price'

    def subtotal_display(self, obj):
        """Display subtotal"""
        return f"${obj.subtotal:.2f}"
    subtotal_display.short_description = 'Subtotal'

    def availability_status(self, obj):
        """Display availability status with color"""
        if obj.is_available:
            return format_html('<span style="color: green; font-weight: bold;">✓ Available</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">✗ Unavailable</span>')
    availability_status.short_description = 'Status'

    def variation_details(self, obj):
        """Display variation details"""
        details = obj.variation_details
        if details:
            return format_html('<pre>{}</pre>', str(details))
        return 'No variation'
    variation_details.short_description = 'Variation Details'

    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('cart__user', 'product', 'product_variation')

    actions = ['remove_unavailable_items']

    def remove_unavailable_items(self, request, queryset):
        """Admin action to remove unavailable items"""
        unavailable_items = [item for item in queryset if not item.is_available]
        count = len(unavailable_items)
        
        for item in unavailable_items:
            item.delete()
        
        self.message_user(request, f'{count} unavailable items were removed from carts.')
    remove_unavailable_items.short_description = 'Remove unavailable items'
