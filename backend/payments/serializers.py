from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    order_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'user', 'payment_method', 'payment_reference',
            'amount', 'status', 'transaction_id', 'gateway_response',
            'order_details', 'created_at', 'updated_at', 'paid_at'
        ]
        read_only_fields = ['payment_reference', 'paid_at']

    def get_order_details(self, obj):
        """Return basic order information"""
        return {
            'order_number': obj.order.order_number,
            'total_amount': obj.order.total_amount,
            'status': obj.order.status
        }

    def validate_amount(self, value):
        """Validate payment amount"""
        if value <= 0:
            raise serializers.ValidationError("Payment amount must be greater than zero")
        return value


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payments"""
    
    class Meta:
        model = Payment
        fields = ['order', 'payment_method', 'amount', 'transaction_id']

    def validate(self, attrs):
        """Validate payment data"""
        order = attrs['order']
        amount = attrs['amount']
        
        # Check if user owns the order
        user = self.context['request'].user
        if order.user != user:
            raise serializers.ValidationError({
                'order': 'You can only create payments for your own orders'
            })
        
        # Check if amount matches order total
        if amount != order.total_amount:
            raise serializers.ValidationError({
                'amount': f'Payment amount must match order total: {order.total_amount}'
            })
        
        return attrs

    def create(self, validated_data):
        """Create payment"""
        user = self.context['request'].user
        return Payment.objects.create(user=user, **validated_data)