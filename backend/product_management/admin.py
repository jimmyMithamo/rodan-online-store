from django.contrib import admin
from .models import (
    Banner, Category, Tag, Brand, ProductAttribute, AttributeValue, 
    Product, ProductVariation, ProductVariationValue, Review, ProductImage
)

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'subtitle', 'badge_text', 'is_active', 
        'display_order', 'cta_text', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'subtitle', 'badge_text']
    ordering = ['display_order', '-created_at']
    list_editable = ['is_active', 'display_order']
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'subtitle', 'badge_text')
        }),
        ('Styling', {
            'fields': ('background_color', 'text_color')
        }),
        ('Images', {
            'fields': ('background_image', 'background_image_url'),
            'description': '''
                <strong>Image Requirements:</strong><br>
                • Minimum size: 1920x600 pixels<br>
                • Recommended size: 2560x800 pixels<br>
                • Aspect ratio: 2.5:1 to 4:1 (landscape)<br>
                • Format: JPG, PNG, WebP<br>
                • Use either background image upload OR external URL (not both)
            '''
        }),
        ('Call to Action', {
            'fields': ('cta_text', 'cta_link')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'display_order')
        }),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'parent', 'get_hierarchy', 
         'has_image', 'created_at'
    ]
    list_filter = ['parent', 'created_at']
    search_fields = ['name', 'description', 'meta_title']
    ordering = ['name']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'parent', 'description')
        }),
        ('Images & Icons', {
            'fields': ('image', 'image_url'),
            'description': 'Either upload an image file or provide an external URL'
        }),
        
    )

    def has_image(self, obj):
        """Display whether category has an image"""
        return bool(obj.image_source)
    has_image.boolean = True
    has_image.short_description = 'Has Image'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_count', 'created_at', 'updated_at']
    search_fields = ['name']
    ordering = ['name']

    def product_count(self, obj):
        """Display the number of products for this brand"""
        return obj.product_count
    product_count.short_description = 'Products'

@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']

@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ['attribute', 'value', 'created_at']
    list_filter = ['attribute']
    search_fields = ['attribute__name', 'value']
    ordering = ['attribute__name', 'value']

class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 0
    fields = ['sku', 'price', 'stock_quantity', 'is_active']

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'image_url', 'alt_text', 'image_type', 'display_order', 'is_active']

class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    fields = ['user', 'rating', 'review_text', 'is_approved']
    readonly_fields = ['user']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'brand', 'category', 'product_type', 'price', 
        'discounted_price', 'stock_quantity', 'is_in_stock', 
        'rating', 'product_views', 'quantity_sold', 'is_active', 'created_at'
    ]
    list_filter = [
        'product_type', 'category', 'brand', 'is_active', 
        'discount_type', 'created_at'
    ]
    search_fields = ['name', 'brand', 'sku', 'description']
    filter_horizontal = ['tags']
    inlines = [ProductImageInline, ProductVariationInline, ReviewInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'product_type', 'brand', 'sku', 'is_active')
        }),
        ('Categories & Tags', {
            'fields': ('category', 'parent_category', 'tags')
        }),
        ('Content', {
            'fields': ('description', 'product_details', 'additional_information')
        }),
        ('Pricing & Discount', {
            'fields': ('price', 'discount_type', 'discount')
        }),
        ('Inventory', {
            'fields': ('stock_quantity',)
        }),
        ('Statistics', {
            'fields': ('rating', 'product_views', 'quantity_sold'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['rating', 'show_variation_attributes']
    ordering = ['-created_at']
    
    def save_model(self, request, obj, form, change):
        """Save the product and update images field from related ProductImage objects"""
        super().save_model(request, obj, form, change)
        self.update_product_images(obj)
    
    def save_related(self, request, form, formsets, change):
        """Save related objects (including ProductImages) and update images field"""
        super().save_related(request, form, formsets, change)
        self.update_product_images(form.instance)
    
    def update_product_images(self, product):
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

    def show_variation_attributes(self, obj):
        """Show attributes used in product variations"""
        attrs = set()
        if hasattr(obj, 'attributes') and obj.attributes:
            if hasattr(obj.attributes, 'all'):
                attrs.update([a.name for a in obj.attributes.all()])
            elif isinstance(obj.attributes, list):
                attrs.update([getattr(a, 'name', str(a)) for a in obj.attributes])
        for v in obj.variations.all():
            if hasattr(v, 'variations_attributes') and hasattr(v.variations_attributes, 'all'):
                for va in v.variations_attributes.all():
                    attrs.add(getattr(va, 'attribute_name', str(va)))
        return ', '.join(attrs) if attrs else '—'
    show_variation_attributes.short_description = 'Variation Attributes'

class ProductVariationValueInline(admin.TabularInline):
    model = ProductVariationValue
    extra = 1
    fields = ['attribute_value']

@admin.register(ProductVariation)
class ProductVariationAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'sku', 'price', 'discounted_price', 'stock_quantity',
        'display_attributes', 'is_active', 'created_at'
    ]
    list_filter = ['product', 'is_active', 'created_at']
    search_fields = ['product__name', 'sku']
    inlines = [ProductVariationValueInline]
    ordering = ['product', 'sku']

@admin.register(ProductVariationValue)
class ProductVariationValueAdmin(admin.ModelAdmin):
    list_display = ['product_variation', 'attribute_value']
    list_filter = ['attribute_value__attribute']
    search_fields = ['product_variation__sku', 'attribute_value__value']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'user', 'rating', 'is_approved', 'created_at'
    ]
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['product__name', 'user__email', 'review_text']
    readonly_fields = ['user', 'product']
    ordering = ['-created_at']


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'product_variation', 'image_type', 'alt_text', 
        'display_order', 'is_active', 'created_at'
    ]
    list_filter = ['image_type', 'is_active', 'created_at']
    search_fields = ['product__name', 'product_variation__sku', 'alt_text']
    ordering = ['product', 'display_order', 'created_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('product', 'product_variation', 'image_type', 'display_order', 'is_active')
        }),
        ('Image Source', {
            'fields': ('image', 'image_url'),
            'description': 'Either upload an image file or provide an external URL'
        }),
        ('Metadata', {
            'fields': ('alt_text', 'file_size', 'width', 'height'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['file_size', 'width', 'height']
