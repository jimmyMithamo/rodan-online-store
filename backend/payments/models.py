from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('mobile_money', 'Mobile Money'),
    ]

    # We'll import Order when needed to avoid circular imports
    order = models.ForeignKey('order_management.Order', on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)  # Store payment gateway response
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_reference']),
        ]

    def __str__(self):
        return f"Payment {self.payment_reference} - {self.order.order_number}"

    def save(self, *args, **kwargs):
        if not self.payment_reference:
            self.payment_reference = self.generate_payment_reference()
        super().save(*args, **kwargs)

    def generate_payment_reference(self):
        """Generate unique payment reference"""
        import datetime
        from django.utils import timezone
        
        now = timezone.now()
        prefix = f"PAY{now.strftime('%Y%m%d')}"
        
        # Get the last payment reference for today
        last_payment = Payment.objects.filter(
            payment_reference__startswith=prefix,
            created_at__date=now.date()
        ).order_by('-payment_reference').first()
        
        if last_payment:
            last_sequence = int(last_payment.payment_reference[-6:])
            sequence = last_sequence + 1
        else:
            sequence = 1
        
        return f"{prefix}{sequence:06d}"
