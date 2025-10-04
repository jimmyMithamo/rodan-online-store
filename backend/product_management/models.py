from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from PIL import Image
import uuid
import re
import string
import random

User = get_user_model()

def generate_sku(name, brand=None, category=None, length=8):
    """
    Generate a unique SKU based on product name, brand, and category
    Format: BRAND-CATEGORY-NAME-RANDOM
    """
    # Helper function to clean and format text
    def clean_text(text):
        if not text:
            return ""
        # Remove special characters and convert to uppercase
        cleaned = re.sub(r'[^a-zA-Z0-9]', '', str(text))
        return cleaned.upper()[:3]  # Take first 3 characters
    
    # Build SKU components
    components = []
    
    if brand:
        components.append(clean_text(brand))
    
    if category:
        components.append(clean_text(category))
    
    # Add product name (first 3-4 characters)
    name_part = clean_text(name)[:4] if name else "PROD"
    components.append(name_part)
    
    # Add random component
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    components.append(random_part)
    
    # Join with hyphens and ensure it's not too long
    sku = '-'.join(filter(None, components))
    
    # Truncate if too long, keeping the random part
    if len(sku) > 50:
        # Keep last part (random) and truncate middle parts
        parts = sku.split('-')
        random_suffix = parts[-1]
        prefix_parts = parts[:-1]
        
        # Calculate available space for prefix
        available_space = 50 - len(random_suffix) - 1  # -1 for the hyphen
        
        # Truncate prefix parts
        prefix = '-'.join(prefix_parts)
        if len(prefix) > available_space:
            prefix = prefix[:available_space]
        
        sku = f"{prefix}-{random_suffix}"
    
    return sku

def ensure_unique_sku(sku, model_class, exclude_id=None):
    """
    Ensure SKU is unique by appending numbers if necessary
    """
    original_sku = sku
    counter = 1
    
    while True:
        # Check if SKU exists
        queryset = model_class.objects.filter(sku=sku)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        
        if not queryset.exists():
            return sku
        
        # If exists, append counter
        sku = f"{original_sku}-{counter:02d}"
        counter += 1
        
        # Prevent infinite loop
        if counter > 999:
            # Add timestamp as last resort
            import time
            timestamp = str(int(time.time()))[-6:]
            sku = f"{original_sku}-{timestamp}"
            break
    
    return sku

def validate_banner_image(image):
    """Validate banner image dimensions for quality"""
    if image:
        try:
            img = Image.open(image)
            width, height = img.size
            
            # Minimum dimensions for quality
            MIN_WIDTH = 1920
            MIN_HEIGHT = 600
            
            if width < MIN_WIDTH:
                raise ValidationError(f'Image width must be at least {MIN_WIDTH}px. Current width: {width}px')
            
            if height < MIN_HEIGHT:
                raise ValidationError(f'Image height must be at least {MIN_HEIGHT}px. Current height: {height}px')
            
            # Check aspect ratio (should be between 2.5:1 and 4:1)
            aspect_ratio = width / height
            if aspect_ratio < 2.5 or aspect_ratio > 4.0:
                raise ValidationError(f'Image aspect ratio should be between 2.5:1 and 4:1. Current ratio: {aspect_ratio:.2f}:1')
                
        except Exception as e:
            if isinstance(e, ValidationError):
                raise e
            raise ValidationError('Invalid image file')

class Banner(models.Model):
    """Model for dynamic banner sliders"""
    title = models.CharField(max_length=200, help_text="Main banner title")
    subtitle = models.CharField(max_length=200, help_text="Banner subtitle/description")
    badge_text = models.CharField(max_length=100, blank=True, help_text="Badge text (e.g., 'NEW ARRIVAL', 'SALE')")
    
    # Background styling
    background_color = models.CharField(
        max_length=100, 
        default="bg-gradient-to-r from-blue-900 to-blue-700",
        help_text="Tailwind CSS background classes"
    )
    text_color = models.CharField(
        max_length=50,
        default="text-white",
        help_text="Tailwind CSS text color classes"
    )
    
    # Images
    background_image = models.ImageField(
        upload_to='banners/backgrounds/%Y/%m/', 
        blank=True, 
        null=True,
        validators=[validate_banner_image],
        help_text="Minimum size: 1920x600px. Recommended: 2560x800px. Aspect ratio: 2.5:1 to 4:1"
    )
    background_image_url = models.URLField(max_length=500, blank=True, help_text="External background image URL")
    
    # CTA (Call to Action)
    cta_text = models.CharField(max_length=50, default="Shop Now", help_text="Button text")
    cta_link = models.CharField(max_length=200, default="/products", help_text="Link URL for the button")
    
    # Control
    is_active = models.BooleanField(default=True, help_text="Whether this banner is active")
    display_order = models.IntegerField(default=0, help_text="Order in which banners appear (lower numbers first)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = "Banner"
        verbose_name_plural = "Banners"
    
    def __str__(self):
        return f"{self.title} - {self.subtitle}"
    
    @property
    def background_image_source(self):
        """Return the appropriate background image source (file or URL)"""
        if self.background_image:
            return self.background_image.url
        elif self.background_image_url:
            return self.background_image_url
        return None

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    description = models.TextField(blank=True, help_text="Category description")
    image = models.ImageField(upload_to='categories/%Y/%m/', blank=True, null=True, help_text="Category image")
    image_url = models.URLField(max_length=500, blank=True, help_text="External category image URL")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        indexes = [
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return self.name

    @property
    def is_parent(self):
        return self.parent is None

    @property
    def image_source(self):
        """Return the appropriate image source (file or URL)"""
        if self.image:
            return self.image.url
        elif self.image_url:
            return self.image_url
        return None

    def get_hierarchy(self):
        """Return the full category hierarchy"""
        hierarchy = []
        current = self
        while current:
            hierarchy.append(current.name)
            current = current.parent
        return ' > '.join(reversed(hierarchy))


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def product_count(self):
        """Return the number of active products for this brand"""
        return self.products.filter(is_active=True).count()


class ProductAttribute(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['attribute', 'value']
        ordering = ['attribute__name', 'value']

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class Product(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('simple', 'Simple'),
        ('variable', 'Variable'),
    ]
    
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount (KES)'),
    ]

    name = models.CharField(max_length=200)
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPE_CHOICES, default='simple')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    parent_category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='parent_products', null=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    description = models.TextField()
    product_details = models.TextField(blank=True)
    additional_information = models.TextField(blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], null=True, blank=True, help_text="Required for simple products, optional for variable products")
    sku = models.CharField(max_length=100, unique=True, blank=True, help_text="Leave blank to auto-generate")
    stock_quantity = models.PositiveIntegerField(default=0, null=True, blank=True, help_text="Required for simple products, calculated from variations for variable products")
    product_views = models.PositiveIntegerField(default=0)
    quantity_sold = models.PositiveIntegerField(default=0)
    images = models.JSONField(default=list, blank=True)  # Store image URLs
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(5)])
    tags = models.ManyToManyField(Tag, blank=True, related_name='products')
    attributes = models.ManyToManyField(ProductAttribute, blank=True, related_name='products')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['brand']),
            models.Index(fields=['is_active']),
            models.Index(fields=['product_type']),
        ]

    def __str__(self):
        return self.name

    @property
    def discounted_price(self):
        """Calculate the price after discount"""
        if self.price is None:
            return 0
        if self.discount_type and self.discount:
            if self.discount_type == 'percentage' and self.discount > 0:
                return self.price * (1 - self.discount / 100)
            elif self.discount_type == 'fixed' and self.discount > 0:
                return max(0, self.price - self.discount)
        return self.price

    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        if self.product_type == 'simple':
            return self.stock_quantity > 0
        else:
            # For variable products, check if any variation is in stock
            return self.variations.filter(stock_quantity__gt=0).exists()

    @property
    def average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0

    def increment_views(self):
        """Increment product views count"""
        self.product_views += 1
        self.save(update_fields=['product_views'])

    def increment_sold(self, quantity=1):
        """Increment quantity sold"""
        self.quantity_sold += quantity
        self.save(update_fields=['quantity_sold'])

    def clean(self):
        """Custom validation for the Product model"""
        super().clean()
        
        # For simple products, price and stock_quantity are required
        if self.product_type == 'simple':
            if self.price is None:
                raise ValidationError({'price': 'Price is required for simple products'})
            if self.stock_quantity is None:
                raise ValidationError({'stock_quantity': 'Stock quantity is required for simple products'})

    def save(self, *args, **kwargs):
        """Override save to auto-generate SKU if not provided"""
        if not self.sku:
            # Generate SKU based on product name, brand, and category
            brand_name = self.brand.name if self.brand else None
            category_name = self.category.name if self.category else None
            
            generated_sku = generate_sku(
                name=self.name,
                brand=brand_name,
                category=category_name
            )
            
            # Ensure SKU is unique
            self.sku = ensure_unique_sku(generated_sku, Product, exclude_id=self.pk)
        
        super().save(*args, **kwargs)

    @property
    def variation_attributes(self):
        """Get unique attributes used in this product's variations"""
        if self.product_type != 'variable':
            return ProductAttribute.objects.none()
        
        # Get all attribute values used in variations
        attribute_values = AttributeValue.objects.filter(
            variations__product=self
        ).select_related('attribute').distinct()
        
        # Group by attribute and return ProductAttribute objects with their values
        attributes_dict = {}
        for av in attribute_values:
            if av.attribute.id not in attributes_dict:
                attributes_dict[av.attribute.id] = av.attribute
        
        return list(attributes_dict.values())
    
    


class ProductVariation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variations')
    sku = models.CharField(max_length=100, unique=True, blank=True, help_text="Leave blank to auto-generate")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    discount_type = models.CharField(max_length=10, choices=Product.DISCOUNT_TYPE_CHOICES, null=True, blank=True)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock_quantity = models.PositiveIntegerField(default=0)
    images = models.JSONField(default=list, blank=True)  # Fallback to product images if empty
    attribute_values = models.ManyToManyField(AttributeValue, through='ProductVariationValue', related_name='variations')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['product', 'sku']

    def __str__(self):
        return f"{self.product.name} - {self.sku}"

    @property
    def discounted_price(self):
        """Calculate the price after discount"""
        if self.price is None:
            return 0
        if self.discount_type and self.discount:
            if self.discount_type == 'percentage' and self.discount > 0:
                return self.price * (1 - self.discount / 100)
            elif self.discount_type == 'fixed' and self.discount > 0:
                return max(0, self.price - self.discount)
        return self.price

    @property
    def is_in_stock(self):
        """Check if this variation is in stock"""
        return self.stock_quantity > 0

    @property
    def display_attributes(self):
        """Return a formatted string of attribute values"""
        values = self.attribute_values.all()
        return ', '.join([f"{val.attribute.name}: {val.value}" for val in values])

    @property
    def effective_images(self):
        """Return variation images or fallback to product images"""
        return self.images if self.images else self.product.images

    def save(self, *args, **kwargs):
        """Override save to auto-generate SKU if not provided"""
        if not self.sku:
            # Generate SKU based on product info and variation attributes
            brand_name = self.product.brand.name if self.product.brand else None
            category_name = self.product.category.name if self.product.category else None
            
            # Get attribute values for this variation to include in SKU
            if self.pk:  # Only if the variation already exists (has relations)
                try:
                    attribute_values = self.attribute_values.all()
                    variation_suffix = '-'.join([val.value for val in attribute_values])[:10]  # Limit length
                    if variation_suffix:
                        variation_suffix = f"-{variation_suffix}"
                except:
                    variation_suffix = ""
            else:
                variation_suffix = ""
            
            # Generate base SKU
            base_name = f"{self.product.name}{variation_suffix}"
            generated_sku = generate_sku(
                name=base_name,
                brand=brand_name,
                category=category_name
            )
            
            # Ensure SKU is unique
            self.sku = ensure_unique_sku(generated_sku, ProductVariation, exclude_id=self.pk)
        
        super().save(*args, **kwargs)


class ProductVariationValue(models.Model):
    """Junction table for ProductVariation and AttributeValue many-to-many relationship"""
    product_variation = models.ForeignKey(ProductVariation, on_delete=models.CASCADE)
    attribute_value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['product_variation', 'attribute_value']

    def __str__(self):
        return f"{self.product_variation.sku} - {self.attribute_value}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    review_text = models.TextField()
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'user']  # One review per user per product
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user.email} for {self.product.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update product rating when review is saved
        self.product.rating = self.product.average_rating
        self.product.save(update_fields=['rating'])


class ProductImage(models.Model):
    """Model for storing product images with metadata"""
    
    IMAGE_TYPE_CHOICES = [
        ('main', 'Main Image'),
        ('gallery', 'Gallery Image'),
        ('thumbnail', 'Thumbnail'),
        ('variant', 'Variant Image'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_images')
    product_variation = models.ForeignKey(ProductVariation, on_delete=models.CASCADE, null=True, blank=True, related_name='variation_images')
    image = models.ImageField(upload_to='products/%Y/%m/', help_text="Product image file")
    image_url = models.URLField(max_length=500, blank=True, help_text="External image URL (if not uploading file)")
    alt_text = models.CharField(max_length=200, blank=True, help_text="Alternative text for accessibility")
    image_type = models.CharField(max_length=10, choices=IMAGE_TYPE_CHOICES, default='gallery')
    display_order = models.PositiveIntegerField(default=0, help_text="Order in which images are displayed")
    is_active = models.BooleanField(default=True)
    file_size = models.PositiveIntegerField(null=True, blank=True, help_text="File size in bytes")
    width = models.PositiveIntegerField(null=True, blank=True, help_text="Image width in pixels")
    height = models.PositiveIntegerField(null=True, blank=True, help_text="Image height in pixels")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['product', 'display_order', 'created_at']
        indexes = [
            models.Index(fields=['product', 'image_type']),
            models.Index(fields=['product_variation', 'image_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        if self.product_variation:
            return f"{self.product.name} ({self.product_variation.sku}) - {self.get_image_type_display()}"
        return f"{self.product.name} - {self.get_image_type_display()}"

    @property
    def image_source(self):
        """Return the appropriate image source (file or URL)"""
        if self.image:
            return self.image.url
        elif self.image_url:
            return self.image_url
        return None

    def save(self, *args, **kwargs):
        # Set alt_text to product name if not provided
        if not self.alt_text:
            if self.product_variation:
                self.alt_text = f"{self.product.name} - {self.product_variation.display_attributes}"
            else:
                self.alt_text = self.product.name
        
        # Set file metadata if image is uploaded
        if self.image:
            self.file_size = self.image.size
            # Note: For width/height, you might want to use PIL to get dimensions
            # from PIL import Image
            # img = Image.open(self.image)
            # self.width, self.height = img.size
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the physical file when model instance is deleted
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)


# Signal handlers to automatically update Product.images field
def update_product_images(product):
    """Update the product's images JSONField with URLs from ProductImage objects"""
    # Get all active ProductImage objects for this product
    product_images = ProductImage.objects.filter(
        product=product, 
        is_active=True
    ).order_by('display_order', 'created_at')
    
    image_urls = []
    for img in product_images:
        if img.image:
            # For uploaded files, get the URL
            image_urls.append(img.image.url)
        elif img.image_url:
            # For external URLs
            image_urls.append(img.image_url)
    
    # Update the product's images field
    if image_urls != product.images:
        product.images = image_urls
        product.save(update_fields=['images'])

@receiver(post_save, sender=ProductImage)
def product_image_saved(sender, instance, **kwargs):
    """Update product images when a ProductImage is saved"""
    update_product_images(instance.product)

@receiver(post_delete, sender=ProductImage)
def product_image_deleted(sender, instance, **kwargs):
    """Update product images when a ProductImage is deleted"""
    update_product_images(instance.product)

