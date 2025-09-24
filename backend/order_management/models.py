from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
from product_management.models import Product, ProductVariation, Category

User = get_user_model()


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('free_shipping', 'Free Shipping'),
    ]

    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Total usage limit for this coupon")
    usage_limit_per_user = models.PositiveIntegerField(default=1, help_text="Usage limit per user")
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    applicable_products = models.ManyToManyField(Product, blank=True, related_name='coupons')
    applicable_categories = models.ManyToManyField(Category, blank=True, related_name='coupons')
    times_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.code} - {self.get_discount_type_display()}"

    @property
    def is_valid(self):
        """Check if coupon is currently valid"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now <= self.end_date and
            (self.usage_limit is None or self.times_used < self.usage_limit)
        )

    def can_be_used_by_user(self, user):
        """Check if user can use this coupon"""
        if not self.is_valid:
            return False
        
        user_usage = CouponUsage.objects.filter(coupon=self, user=user).count()
        return user_usage < self.usage_limit_per_user

    def get_discount_amount(self, order_total):
        """Calculate discount amount for given order total"""
        if self.discount_type == 'percentage':
            return min(order_total * (self.discount_value / 100), order_total)
        elif self.discount_type == 'fixed':
            return min(self.discount_value, order_total)
        elif self.discount_type == 'free_shipping':
            return Decimal('0')  # Free shipping handled separately
        return Decimal('0')


class Order(models.Model):
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash_on_delivery', 'Cash on Delivery'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    
    # Address information
    shipping_first_name = models.CharField(max_length=100)
    shipping_last_name = models.CharField(max_length=100)
    shipping_email = models.EmailField()
    shipping_phone = models.CharField(max_length=20)
    shipping_address_line_1 = models.CharField(max_length=255)
    shipping_address_line_2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, default='Kenya')
    
    # Order totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Coupon information
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    coupon_code = models.CharField(max_length=50, blank=True)  # Store for history
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Additional fields
    notes = models.TextField(blank=True, help_text="Special instructions or notes")
    tracking_number = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['order_number']),
        ]

    def __str__(self):
        return f"Order {self.order_number} - {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        """Generate unique order number"""
        import datetime
        from django.utils import timezone
        
        now = timezone.now()
        prefix = f"ORD{now.strftime('%Y%m%d')}"
        
        # Get the last order number for today
        last_order = Order.objects.filter(
            order_number__startswith=prefix,
            created_at__date=now.date()
        ).order_by('-order_number').first()
        
        if last_order:
            last_sequence = int(last_order.order_number[-4:])
            sequence = last_sequence + 1
        else:
            sequence = 1
        
        return f"{prefix}{sequence:04d}"

    def calculate_totals(self):
        """Calculate order totals"""
        self.subtotal = sum(item.subtotal for item in self.items.all())
        
        # Apply coupon discount
        if self.coupon and self.coupon.is_valid:
            if self.subtotal >= self.coupon.minimum_order_amount:
                self.discount_amount = self.coupon.get_discount_amount(self.subtotal)
            else:
                self.discount_amount = Decimal('0')
        else:
            self.discount_amount = Decimal('0')
        
        # Calculate total
        self.total_amount = self.subtotal + self.shipping_cost + self.tax_amount - self.discount_amount
        self.save(update_fields=['subtotal', 'discount_amount', 'total_amount'])

    @property
    def full_shipping_address(self):
        """Return formatted shipping address"""
        address_parts = [
            f"{self.shipping_first_name} {self.shipping_last_name}",
            self.shipping_address_line_1,
        ]
        if self.shipping_address_line_2:
            address_parts.append(self.shipping_address_line_2)
        address_parts.extend([
            self.shipping_city,
            self.shipping_postal_code,
            self.shipping_country
        ])
        return ", ".join(filter(None, address_parts))

    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in ['created', 'confirmed']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_variation = models.ForeignKey(ProductVariation, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Store product details for historical purposes
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=100)
    variation_details = models.JSONField(default=dict, blank=True)  # Store variation attributes
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['order', 'product', 'product_variation']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f"{self.product_name} x{self.quantity} - Order {self.order.order_number}"

    def save(self, *args, **kwargs):
        # Store product details at time of order
        self.product_name = self.product.name
        self.product_sku = self.product_variation.sku if self.product_variation else self.product.sku
        
        # Store variation details
        if self.product_variation:
            self.variation_details = {
                'sku': self.product_variation.sku,
                'attributes': self.product_variation.display_attributes
            }
        
        # Calculate subtotal
        self.subtotal = self.unit_price * self.quantity
        
        super().save(*args, **kwargs)
        
        # Update order totals
        self.order.calculate_totals()


class CouponUsage(models.Model):
    """Track coupon usage by users"""
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupon_usages')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='coupon_usages')
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['coupon', 'user', 'order']
        indexes = [
            models.Index(fields=['coupon']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.coupon.code} used by {self.user.email}"
