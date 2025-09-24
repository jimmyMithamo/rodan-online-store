from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Order, OrderItem, Coupon, CouponUsage
from payments.models import Payment
from payments.serializers import PaymentSerializer
from core.models import AuditLog
from core.serializers import AuditLogSerializer
from product_management.models import Product, ProductVariation
from product_management.serializers import ProductListSerializer, ProductVariationSerializer

User = get_user_model()


class CouponSerializer(serializers.ModelSerializer):
    is_currently_valid = serializers.ReadOnlyField(source='is_valid')
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'description', 'discount_type', 'discount_value',
            'usage_limit', 'usage_limit_per_user', 'minimum_order_amount',
            'start_date', 'end_date', 'is_active', 'times_used',
            'is_currently_valid', 'created_at', 'updated_at'
        ]
        read_only_fields = ['times_used', 'is_currently_valid']

    def validate(self, attrs):
        """Validate coupon dates and discount value"""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        discount_type = attrs.get('discount_type')
        discount_value = attrs.get('discount_value')

        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date'
            })

        if discount_type == 'percentage' and discount_value > 100:
            raise serializers.ValidationError({
                'discount_value': 'Percentage discount cannot exceed 100%'
            })

        if discount_value < 0:
            raise serializers.ValidationError({
                'discount_value': 'Discount value cannot be negative'
            })

        return attrs


class CouponValidationSerializer(serializers.Serializer):
    """Serializer for validating coupon codes"""
    code = serializers.CharField(max_length=50)
    order_total = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    def validate_code(self, value):
        """Validate coupon code exists and is active"""
        try:
            coupon = Coupon.objects.get(code=value.upper())
            return coupon
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid coupon code")

    def validate(self, attrs):
        """Validate coupon can be used"""
        coupon = attrs['code']  # This is now a Coupon object
        user = self.context['request'].user
        order_total = attrs.get('order_total', Decimal('0'))

        if not coupon.is_valid:
            raise serializers.ValidationError({
                'code': 'This coupon is not currently valid'
            })

        if not coupon.can_be_used_by_user(user):
            raise serializers.ValidationError({
                'code': 'You have reached the usage limit for this coupon'
            })

        if order_total < coupon.minimum_order_amount:
            raise serializers.ValidationError({
                'code': f'Minimum order amount of {coupon.minimum_order_amount} required'
            })

        attrs['coupon'] = coupon
        return attrs


class OrderItemSerializer(serializers.ModelSerializer):
    product_details = ProductListSerializer(source='product', read_only=True)
    variation_details = ProductVariationSerializer(source='product_variation', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_variation', 'quantity', 'unit_price',
            'subtotal', 'product_name', 'product_sku', 'variation_details',
            'product_details', 'created_at'
        ]
        read_only_fields = ['subtotal', 'product_name', 'product_sku']

    def validate(self, attrs):
        """Validate order item data"""
        product = attrs['product']
        product_variation = attrs.get('product_variation')
        quantity = attrs['quantity']

        # Validate product variation belongs to product
        if product_variation and product_variation.product != product:
            raise serializers.ValidationError({
                'product_variation': 'Product variation does not belong to the selected product'
            })

        # Check stock availability
        if product_variation:
            available_stock = product_variation.stock_quantity
            if quantity > available_stock:
                raise serializers.ValidationError({
                    'quantity': f'Only {available_stock} items available in stock'
                })
        else:
            available_stock = product.stock_quantity
            if quantity > available_stock:
                raise serializers.ValidationError({
                    'quantity': f'Only {available_stock} items available in stock'
                })

        return attrs


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating order items"""
    
    class Meta:
        model = OrderItem
        fields = ['product', 'product_variation', 'quantity', 'unit_price']

    def validate(self, attrs):
        """Validate and set unit price"""
        product = attrs['product']
        product_variation = attrs.get('product_variation')
        
        # Set unit price from product or variation
        if product_variation:
            attrs['unit_price'] = product_variation.price
        else:
            attrs['unit_price'] = product.discounted_price
        
        return super().validate(attrs)


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for order list view"""
    items_count = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'payment_method', 'total_amount',
            'items_count', 'payment_status', 'created_at', 'updated_at'
        ]

    def get_items_count(self, obj):
        """Return number of items in order"""
        return obj.items.count()

    def get_payment_status(self, obj):
        """Return latest payment status"""
        latest_payment = obj.payments.first()
        return latest_payment.status if latest_payment else None


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for order detail view"""
    items = OrderItemSerializer(many=True, read_only=True)
    coupon_details = CouponSerializer(source='coupon', read_only=True)
    payments = serializers.SerializerMethodField()
    can_be_cancelled = serializers.ReadOnlyField()
    full_shipping_address = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'status', 'payment_method',
            'shipping_first_name', 'shipping_last_name', 'shipping_email',
            'shipping_phone', 'shipping_address_line_1', 'shipping_address_line_2',
            'shipping_city', 'shipping_postal_code', 'shipping_country',
            'full_shipping_address', 'subtotal', 'shipping_cost', 'tax_amount',
            'discount_amount', 'total_amount', 'coupon', 'coupon_code',
            'coupon_details', 'notes', 'tracking_number', 'items', 'payments',
            'can_be_cancelled', 'created_at', 'updated_at', 'confirmed_at',
            'shipped_at', 'delivered_at'
        ]

    def get_payments(self, obj):
        """Return order payments"""
        return PaymentSerializer(obj.payments.all(), many=True).data


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders"""
    items = OrderItemCreateSerializer(many=True)
    coupon_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    class Meta:
        model = Order
        fields = [
            'payment_method', 'shipping_first_name', 'shipping_last_name',
            'shipping_email', 'shipping_phone', 'shipping_address_line_1',
            'shipping_address_line_2', 'shipping_city', 'shipping_postal_code',
            'shipping_country', 'shipping_cost', 'tax_amount', 'notes',
            'items', 'coupon_code'
        ]

    def validate_items(self, value):
        """Validate order has items"""
        if not value:
            raise serializers.ValidationError("Order must have at least one item")
        return value

    def validate_coupon_code(self, value):
        """Validate coupon code if provided"""
        if value:
            try:
                coupon = Coupon.objects.get(code=value.upper())
                if not coupon.is_valid:
                    raise serializers.ValidationError("Invalid or expired coupon code")
                return coupon
            except Coupon.DoesNotExist:
                raise serializers.ValidationError("Invalid coupon code")
        return None

    def create(self, validated_data):
        """Create order with items"""
        items_data = validated_data.pop('items')
        coupon = validated_data.pop('coupon_code', None)
        user = self.context['request'].user
        
        # Create order
        order = Order.objects.create(user=user, **validated_data)
        
        # Add coupon if provided
        if coupon:
            if coupon.can_be_used_by_user(user):
                order.coupon = coupon
                order.coupon_code = coupon.code
                order.save()
                
                # Create coupon usage record
                CouponUsage.objects.create(
                    coupon=coupon,
                    user=user,
                    order=order
                )
                
                # Increment coupon usage
                coupon.times_used += 1
                coupon.save()
        
        # Create order items
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        # Calculate totals
        order.calculate_totals()
        
        return order


class CheckoutSerializer(serializers.Serializer):
    """Serializer for checkout from cart"""
    shipping_first_name = serializers.CharField(max_length=100)
    shipping_last_name = serializers.CharField(max_length=100)
    shipping_email = serializers.EmailField()
    shipping_phone = serializers.CharField(max_length=20)
    shipping_address_line_1 = serializers.CharField(max_length=255)
    shipping_address_line_2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    shipping_city = serializers.CharField(max_length=100)
    shipping_postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    shipping_country = serializers.CharField(max_length=100, default='Kenya')
    shipping_cost = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = serializers.CharField(max_length=20, default='cash_on_delivery')
    notes = serializers.CharField(required=False, allow_blank=True)
    coupon_code = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate_payment_method(self, value):
        """Validate payment method"""
        valid_methods = ['cash_on_delivery', 'mpesa', 'card', 'bank_transfer']
        if value not in valid_methods:
            raise serializers.ValidationError(f"Payment method must be one of: {', '.join(valid_methods)}")
        return value

    def validate_coupon_code(self, value):
        """Validate coupon code if provided"""
        if value:
            try:
                coupon = Coupon.objects.get(code=value.upper())
                if not coupon.is_valid:
                    raise serializers.ValidationError("Invalid or expired coupon code")
                return value
            except Coupon.DoesNotExist:
                raise serializers.ValidationError("Invalid coupon code")
        return value


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating orders"""
    
    class Meta:
        model = Order
        fields = [
            'status', 'payment_method', 'shipping_cost', 'tax_amount',
            'notes', 'tracking_number'
        ]

    def validate_status(self, value):
        """Validate status transitions"""
        if self.instance:
            current_status = self.instance.status
            
            # Define allowed status transitions
            allowed_transitions = {
                'created': ['confirmed', 'cancelled'],
                'confirmed': ['processing', 'cancelled'],
                'processing': ['shipped', 'cancelled'],
                'shipped': ['delivered'],
                'delivered': [],
                'cancelled': [],
                'refunded': []
            }
            
            if value not in allowed_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Cannot change status from {current_status} to {value}"
                )
        
        return value

    def update(self, instance, validated_data):
        """Update order and set timestamps"""
        status = validated_data.get('status')
        
        if status:
            if status == 'confirmed' and not instance.confirmed_at:
                instance.confirmed_at = timezone.now()
            elif status == 'shipped' and not instance.shipped_at:
                instance.shipped_at = timezone.now()
            elif status == 'delivered' and not instance.delivered_at:
                instance.delivered_at = timezone.now()
        
        return super().update(instance, validated_data)


class CouponUsageSerializer(serializers.ModelSerializer):
    coupon_details = CouponSerializer(source='coupon', read_only=True)
    order_details = OrderListSerializer(source='order', read_only=True)
    
    class Meta:
        model = CouponUsage
        fields = [
            'id', 'coupon', 'user', 'order', 'coupon_details',
            'order_details', 'used_at'
        ]