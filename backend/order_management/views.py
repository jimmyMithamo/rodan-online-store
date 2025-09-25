from django.db.models import Q, Count, Sum, F
from django.utils import timezone
from decimal import Decimal
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from .models import Order, OrderItem, Coupon, CouponUsage
from payments.models import Payment
from core.models import AuditLog
from .serializers import (
    OrderListSerializer, OrderDetailSerializer, OrderCreateSerializer,
    OrderUpdateSerializer, OrderItemSerializer, CouponSerializer,
    CouponValidationSerializer, CouponUsageSerializer
)
from payments.serializers import PaymentSerializer, PaymentCreateSerializer
from core.serializers import AuditLogSerializer
from .permissions import IsOwnerOrAdmin, IsOrderOwnerOrAdmin


class OrderFilter(django_filters.FilterSet):
    """Filter for Order model"""
    status = django_filters.MultipleChoiceFilter(choices=Order.STATUS_CHOICES)
    payment_method = django_filters.MultipleChoiceFilter(choices=Order.PAYMENT_METHOD_CHOICES)
    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    total_min = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    total_max = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte')
    has_coupon = django_filters.BooleanFilter(method='filter_has_coupon')
    
    class Meta:
        model = Order
        fields = ['status', 'payment_method', 'date_from', 'date_to', 'total_min', 'total_max', 'has_coupon']

    def filter_has_coupon(self, queryset, name, value):
        """Filter orders that have or don't have coupons"""
        if value:
            return queryset.filter(coupon__isnull=False)
        return queryset.filter(coupon__isnull=True)


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Order model"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OrderFilter
    search_fields = ['order_number', 'shipping_email', 'shipping_first_name', 'shipping_last_name']
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return orders for current user or all for admin"""
        if self.request.user.is_staff:
            return Order.objects.all().prefetch_related('items', 'payments')
        return Order.objects.filter(user=self.request.user).prefetch_related('items', 'payments')

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return OrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        return OrderDetailSerializer

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsOrderOwnerOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order"""
        order = self.get_object()
        
        if not order.can_be_cancelled:
            return Response(
                {'error': 'Order cannot be cancelled in its current status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'cancelled'
        order.save()
        
        # Log the cancellation
        AuditLog.objects.create(
            user=request.user,
            ip_address=self.get_client_ip(request),
            action='cancel_order',
            details=f'Order {order.order_number} cancelled'
        )
        
        return Response({'message': 'Order cancelled successfully'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def confirm(self, request, pk=None):
        """Confirm an order (admin only)"""
        order = self.get_object()
        
        if order.status != 'created':
            return Response(
                {'error': 'Only created orders can be confirmed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'confirmed'
        order.confirmed_at = timezone.now()
        order.save()
        
        AuditLog.objects.create(
            user=request.user,
            ip_address=self.get_client_ip(request),
            action='confirm_order',
            details=f'Order {order.order_number} confirmed'
        )
        
        return Response({'message': 'Order confirmed successfully'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def ship(self, request, pk=None):
        """Ship an order (admin only)"""
        order = self.get_object()
        tracking_number = request.data.get('tracking_number')
        
        if order.status not in ['confirmed', 'processing']:
            return Response(
                {'error': 'Only confirmed or processing orders can be shipped'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'shipped'
        order.shipped_at = timezone.now()
        if tracking_number:
            order.tracking_number = tracking_number
        order.save()
        
        AuditLog.objects.create(
            user=request.user,
            ip_address=self.get_client_ip(request),
            action='ship_order',
            details=f'Order {order.order_number} shipped with tracking: {tracking_number}'
        )
        
        return Response({'message': 'Order shipped successfully'})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get order statistics for current user"""
        queryset = self.get_queryset()
        
        stats = {
            'total_orders': queryset.count(),
            'total_spent': queryset.aggregate(total=Sum('total_amount'))['total'] or Decimal('0'),
            'orders_by_status': {}
        }
        
        # Count orders by status
        for choice in Order.STATUS_CHOICES:
            status_key = choice[0]
            count = queryset.filter(status=status_key).count()
            stats['orders_by_status'][status_key] = count
        
        return Response(stats)

    @action(detail=False, methods=['post'])
    def create_from_cart(self, request):
        """Create order from user's cart"""
        from cart_management.models import Cart
        
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response(
                {'error': 'No cart found for user'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not cart.items.exists():
            return Response(
                {'error': 'Cart is empty'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate required shipping information
        required_fields = [
            'shipping_first_name', 'shipping_last_name', 'shipping_email',
            'shipping_phone', 'shipping_address_line_1', 'shipping_city'
        ]
        
        shipping_data = {}
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {'error': f'{field} is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            shipping_data[field] = request.data[field]
        
        # Optional fields
        optional_fields = [
            'shipping_address_line_2', 'shipping_postal_code', 'shipping_country',
            'shipping_cost', 'tax_amount', 'notes', 'coupon_code', 'payment_method'
        ]
        
        for field in optional_fields:
            if field in request.data:
                shipping_data[field] = request.data[field]
        
        # Set defaults
        shipping_data.setdefault('shipping_country', 'Kenya')
        shipping_data.setdefault('shipping_cost', 0)
        shipping_data.setdefault('tax_amount', 0)
        shipping_data.setdefault('payment_method', 'cash_on_delivery')
        
        # Convert cart items to order items format
        items_data = []
        for cart_item in cart.items.all():
            # Check availability before creating order
            if not cart_item.is_available:
                return Response(
                    {'error': f'Item {cart_item.product_name} is no longer available'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Use discounted price if available
            discounted_price = None
            if cart_item.product_variation and hasattr(cart_item.product_variation, 'discounted_price'):
                discounted_price = cart_item.product_variation.discounted_price
            elif hasattr(cart_item.product, 'discounted_price'):
                discounted_price = cart_item.product.discounted_price

            unit_price = discounted_price if discounted_price and float(discounted_price) < float(cart_item.unit_price) else cart_item.unit_price
            # Round unit_price to 2 decimal places
            try:
                from decimal import Decimal
                unit_price = Decimal(unit_price).quantize(Decimal('0.01'))
            except Exception:
                pass

            item_data = {
                'product': cart_item.product.id,
                'quantity': cart_item.quantity,
                'unit_price': unit_price
            }
            if cart_item.product_variation:
                item_data['product_variation'] = cart_item.product_variation.id
            items_data.append(item_data)
        
        # Create order data
        order_data = {
            **shipping_data,
            'items': items_data
        }
        
        # Create order using existing serializer
        serializer = OrderCreateSerializer(data=order_data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save()
            
            # Clear the cart after successful order creation
            cart.clear_cart()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                ip_address=self.get_client_ip(request),
                action='create_order_from_cart',
                details=f'Order {order.order_number} created from cart'
            )
            
            # Return order details
            return Response({
                'message': 'Order created successfully from cart',
                'id': order.id
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for OrderItem model (read-only)"""
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['order', 'product']
    search_fields = ['product_name', 'product_sku']
    ordering_fields = ['created_at', 'unit_price', 'quantity']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return order items for current user's orders or all for admin"""
        if self.request.user.is_staff:
            return OrderItem.objects.all().select_related('order', 'product', 'product_variation')
        
        return OrderItem.objects.filter(
            order__user=self.request.user
        ).select_related('order', 'product', 'product_variation')


class CouponFilter(django_filters.FilterSet):
    """Filter for Coupon model"""
    discount_type = django_filters.ChoiceFilter(choices=Coupon.DISCOUNT_TYPE_CHOICES)
    is_active = django_filters.BooleanFilter()
    is_valid = django_filters.BooleanFilter(method='filter_is_valid')
    min_discount = django_filters.NumberFilter(field_name='discount_value', lookup_expr='gte')
    max_discount = django_filters.NumberFilter(field_name='discount_value', lookup_expr='lte')
    
    class Meta:
        model = Coupon
        fields = ['discount_type', 'is_active', 'is_valid', 'min_discount', 'max_discount']

    def filter_is_valid(self, queryset, name, value):
        """Filter valid/invalid coupons"""
        now = timezone.now()
        if value:
            return queryset.filter(
                is_active=True,
                start_date__lte=now,
                end_date__gte=now
            ).filter(
                Q(usage_limit__isnull=True) | Q(times_used__lt=F('usage_limit'))
            )
        else:
            return queryset.filter(
                Q(is_active=False) |
                Q(start_date__gt=now) |
                Q(end_date__lt=now) |
                (Q(usage_limit__isnull=False) & Q(times_used__gte=F('usage_limit')))
            )


class CouponViewSet(viewsets.ModelViewSet):
    """ViewSet for Coupon model"""
    serializer_class = CouponSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CouponFilter
    search_fields = ['code', 'description']
    ordering_fields = ['created_at', 'discount_value', 'times_used']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return all coupons for admin"""
        return Coupon.objects.all()

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def validate_coupon(self, request):
        """Validate a coupon code"""
        serializer = CouponValidationSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            coupon = serializer.validated_data['coupon']
            order_total = serializer.validated_data.get('order_total', Decimal('0'))
            
            # Calculate discount
            if coupon.discount_type == 'percentage':
                discount_amount = (order_total * coupon.discount_value) / 100
            else:
                discount_amount = coupon.discount_value
            
            return Response({
                'valid': True,
                'coupon': CouponSerializer(coupon).data,
                'discount_amount': discount_amount,
                'message': 'Coupon is valid'
            })
        
        return Response({
            'valid': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def usage_stats(self, request, pk=None):
        """Get coupon usage statistics"""
        coupon = self.get_object()
        
        stats = {
            'times_used': coupon.times_used,
            'usage_limit': coupon.usage_limit,
            'remaining_uses': coupon.usage_limit - coupon.times_used if coupon.usage_limit else None,
            'total_discount_given': CouponUsage.objects.filter(coupon=coupon).aggregate(
                total=Sum('order__discount_amount')
            )['total'] or Decimal('0'),
            'unique_users': CouponUsage.objects.filter(coupon=coupon).values('user').distinct().count()
        }
        
        return Response(stats)


class CouponUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for CouponUsage model (read-only)"""
    serializer_class = CouponUsageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['coupon', 'user', 'order']
    ordering_fields = ['used_at']
    ordering = ['-used_at']

    def get_queryset(self):
        """Return coupon usage for current user or all for admin"""
        if self.request.user.is_staff:
            return CouponUsage.objects.all().select_related('coupon', 'user', 'order')
        return CouponUsage.objects.filter(user=self.request.user).select_related('coupon', 'order')
