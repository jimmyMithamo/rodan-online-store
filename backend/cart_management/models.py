from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from product_management.models import Product, ProductVariation

User = get_user_model()


class Cart(models.Model):
    """Shopping cart model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['updated_at']),
        ]

    def __str__(self):
        return f"Cart for {self.user.email}"

    @property
    def cart_total(self):
        """Calculate total cart value"""
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_items(self):
        """Count total items in cart"""
        return sum(item.quantity for item in self.items.all())

    @property
    def unique_items_count(self):
        """Count unique items in cart"""
        return self.items.count()

    def clear_cart(self):
        """Remove all items from cart"""
        self.items.all().delete()

    def add_item(self, product, product_variation=None, quantity=1):
        """Add or update item in cart"""
        cart_item, created = CartItem.objects.get_or_create(
            cart=self,
            product=product,
            product_variation=product_variation,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # If item already exists, update quantity
            cart_item.quantity += quantity
            cart_item.save()
        
        return cart_item

    def remove_item(self, product, product_variation=None):
        """Remove item from cart"""
        try:
            cart_item = CartItem.objects.get(
                cart=self,
                product=product,
                product_variation=product_variation
            )
            cart_item.delete()
            return True
        except CartItem.DoesNotExist:
            return False

    def update_item_quantity(self, product, product_variation=None, quantity=1):
        """Update specific item quantity"""
        try:
            cart_item = CartItem.objects.get(
                cart=self,
                product=product,
                product_variation=product_variation
            )
            if quantity <= 0:
                cart_item.delete()
            else:
                cart_item.quantity = quantity
                cart_item.save()
            return cart_item
        except CartItem.DoesNotExist:
            return None


class CartItem(models.Model):
    """Cart item model"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_variation = models.ForeignKey(ProductVariation, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product', 'product_variation']
        indexes = [
            models.Index(fields=['cart']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        variation_str = f" ({self.product_variation.sku})" if self.product_variation else ""
        return f"{self.product.name}{variation_str} x{self.quantity}"

    @property
    def unit_price(self):
        """Get current unit price"""
        if self.product_variation:
            return self.product_variation.price
        return self.product.price

    @property
    def subtotal(self):
        """Calculate cart item subtotal"""
        return self.unit_price * self.quantity

    @property
    def product_name(self):
        """Get product name"""
        return self.product.name

    @property
    def product_sku(self):
        """Get product SKU"""
        if self.product_variation:
            return self.product_variation.sku
        return self.product.sku

    @property
    def variation_details(self):
        """Get variation details if available"""
        if self.product_variation:
            return {
                'sku': self.product_variation.sku,
                'attributes': self.product_variation.display_attributes
            }
        return {}

    @property
    def is_available(self):
        """Check if item is still available"""
        if not self.product.is_active:
            return False
        
        if self.product_variation and not self.product_variation.is_active:
            return False
            
        # Check stock if stock tracking is enabled
        if self.product_variation:
            return self.product_variation.stock_quantity >= self.quantity
        
        return self.product.stock_quantity >= self.quantity

    def save(self, *args, **kwargs):
        """Override save to update cart timestamp"""
        super().save(*args, **kwargs)
        # Update cart's updated_at timestamp
        self.cart.save()

    def delete(self, *args, **kwargs):
        """Override delete to update cart timestamp"""
        cart = self.cart
        super().delete(*args, **kwargs)
        # Update cart's updated_at timestamp
        cart.save()
