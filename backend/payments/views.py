from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from .models import Payment
from .serializers import PaymentSerializer, PaymentCreateSerializer
from core.models import AuditLog


class PaymentFilter(django_filters.FilterSet):
    """Filter for Payment model"""
    status = django_filters.MultipleChoiceFilter(choices=Payment.STATUS_CHOICES)
    payment_method = django_filters.MultipleChoiceFilter(choices=Payment.PAYMENT_METHOD_CHOICES)
    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    
    class Meta:
        model = Payment
        fields = ['status', 'payment_method', 'date_from', 'date_to', 'amount_min', 'amount_max']


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for Payment model"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PaymentFilter
    search_fields = ['payment_reference', 'transaction_id', 'order__order_number']
    ordering_fields = ['created_at', 'amount', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return payments for current user or all for admin"""
        if self.request.user.is_staff:
            return Payment.objects.all().select_related('order', 'user')
        return Payment.objects.filter(user=self.request.user).select_related('order')

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark payment as paid"""
        payment = self.get_object()
        
        # Check permissions
        if not request.user.is_staff and payment.user != request.user:
            return Response(
                {'error': 'You can only modify your own payments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if payment.status == 'completed':
            return Response(
                {'error': 'Payment is already marked as paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment.status = 'completed'
        payment.paid_at = timezone.now()
        payment.save()
        
        # Update order status if needed
        order = payment.order
        if order.status == 'created':
            order.status = 'confirmed'
            order.confirmed_at = timezone.now()
            order.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            ip_address=self.get_client_ip(request),
            action='mark_payment_paid',
            details=f'Payment {payment.payment_reference} marked as paid'
        )
        
        return Response({'message': 'Payment marked as paid successfully'})

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
