from rest_framework import serializers
from .models import (
    Banner, Category, Tag, Brand, ProductAttribute, AttributeValue, 
    Product, ProductVariation, ProductVariationValue, Review, ProductImage
)
from django.db import transaction
from decimal import Decimal, InvalidOperation
import json


class BannerSerializer(serializers.ModelSerializer):
    background_image_source = serializers.ReadOnlyField()
    
    class Meta:
        model = Banner
        fields = [
            'id', 'title', 'subtitle', 'badge_text', 'background_color', 
            'text_color', 'background_image', 'background_image_url', 
            'background_image_source', 'cta_text', 'cta_link', 'is_active', 
            'display_order', 'created_at', 'updated_at'
        ]

class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    hierarchy = serializers.ReadOnlyField(source='get_hierarchy')
    image_source = serializers.ReadOnlyField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'parent', 'description', 'image', 'image_url', 
            'image_source', 'subcategories', 'hierarchy', 
            'created_at', 'updated_at'
        ]

    def get_subcategories(self, obj):
        """Return subcategories if any"""
        if obj.subcategories.exists():
            return CategorySerializer(obj.subcategories.all(), many=True).data
        return []

    def validate_parent(self, value):
        """Prevent circular references in categories"""
        if value and self.instance:
            # Check if the new parent is a descendant of current category
            current = value
            while current:
                if current == self.instance:
                    raise serializers.ValidationError("Cannot set a descendant as parent")
                current = current.parent
        return value

    def validate(self, attrs):
        """Custom validation for image fields"""
        image = attrs.get('image')
        image_url = attrs.get('image_url')
        
        # Both image and image_url can be provided, but warn if both are present
        if image and image_url:
            # This is just a warning, not an error - image takes precedence
            pass
        
        return attrs

    def validate_image_url(self, value):
        """Validate image URL format"""
        if value:
            if not (value.startswith('http://') or value.startswith('https://')):
                raise serializers.ValidationError('Image URL must start with http:// or https://')
        return value

    def validate_display_order(self, value):
        """Validate display order is non-negative"""
        if value < 0:
            raise serializers.ValidationError('Display order must be non-negative')
        return value


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'created_at']

    def validate_name(self, value):
        """Validate tag name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Tag name is required")
        return value.strip().lower()


class BrandSerializer(serializers.ModelSerializer):
    product_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Brand
        fields = ['id', 'name', 'product_count', 'created_at', 'updated_at']

    def validate_name(self, value):
        """Validate brand name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Brand name is required")
        return value.strip()


class ProductAttributeSerializer(serializers.ModelSerializer):
    values = serializers.SerializerMethodField()

    class Meta:
        model = ProductAttribute
        fields = ['id', 'name', 'values', 'created_at']

    def get_values(self, obj):
        """Return attribute values"""
        return AttributeValueSerializer(obj.values.all(), many=True).data


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.ReadOnlyField(source='attribute.name')

    class Meta:
        model = AttributeValue
        fields = ['id', 'attribute', 'attribute_name', 'value', 'created_at']

    def validate_value(self, value):
        """Validate attribute value"""
        if not value or not value.strip():
            raise serializers.ValidationError("Attribute value is required")
        return value.strip()


class ProductVariationValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.ReadOnlyField(source='attribute_value.attribute.name')
    value = serializers.ReadOnlyField(source='attribute_value.value')

    class Meta:
        model = ProductVariationValue
        fields = ['id', 'attribute_name', 'value']


class ProductVariationSerializer(serializers.ModelSerializer):
    variations_attributes = ProductVariationValueSerializer(
        source='productvariationvalue_set', many=True, read_only=True
    )
    attribute_values = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    display_attributes = serializers.ReadOnlyField()
    effective_images = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    sku = serializers.CharField(required=False, allow_blank=True, help_text="Leave blank to auto-generate")
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariation
        fields = [
            'id', 'product', 'sku', 'price', 'discounted_price', 'stock_quantity', 'images',
            'variations_attributes', 'attribute_values', 'display_attributes', 'effective_images',
            'is_in_stock', 'is_active', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        attribute_values = validated_data.pop('attribute_values', [])
        variation = super().create(validated_data)
        
        # Create ProductVariationValue relationships
        for attr_value_id in attribute_values:
            ProductVariationValue.objects.create(
                product_variation=variation,
                attribute_value_id=attr_value_id
            )
        
        return variation

    def update(self, instance, validated_data):
        attribute_values = validated_data.pop('attribute_values', None)
        variation = super().update(instance, validated_data)
        
        if attribute_values is not None:
            # Clear existing relationships
            ProductVariationValue.objects.filter(product_variation=variation).delete()
            
            # Create new relationships
            for attr_value_id in attribute_values:
                ProductVariationValue.objects.create(
                    product_variation=variation,
                    attribute_value_id=attr_value_id
                )
        
        return variation
    def get_discounted_price(self, obj):
        return obj.discounted_price

    def validate_sku(self, value):
        """Validate SKU uniqueness only if provided"""
        # If SKU is not provided or is blank, it will be auto-generated by the model
        if not value or not value.strip():
            return ""  # Return empty string for auto-generation
        
        # Check uniqueness excluding current instance
        queryset = ProductVariation.objects.filter(sku=value.strip())
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("A variation with this SKU already exists")
        
        return value.strip().upper()

    def validate_price(self, value):
        """Validate price"""
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative")
        return value


class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'product', 'user', 'user_email', 'user_name',
            'review_text', 'rating', 'is_approved', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user']

    def get_user_name(self, obj):
        """Return user's full name"""
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

    def validate_rating(self, value):
        """Validate rating range"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def validate_review_text(self, value):
        """Validate review text"""
        if not value or not value.strip():
            raise serializers.ValidationError("Review text is required")
        
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Review must be at least 10 characters long")
        
        return value.strip()

    def create(self, validated_data):
        """Set the user to the request user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product listings"""
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_name = serializers.ReadOnlyField(source='category.name')
    discounted_price = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    review_count = serializers.SerializerMethodField()
    variations = ProductVariationSerializer(many=True, read_only=True)
    rating = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'product_type', 'brand', 'category', 'category_name', 'price', 'discounted_price',
            'discount_type', 'discount', 'images', 'rating', 'review_count',
            'variations', 'is_in_stock', 'is_active', 'product_views', 'quantity_sold', 'stock_quantity']
        

    def get_review_count(self, obj):
        """Return number of approved reviews"""
        return obj.reviews.filter(is_approved=True).count()


class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual product views"""
    category = CategorySerializer(read_only=True)
    parent_category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    attributes = serializers.SerializerMethodField()
    variations = ProductVariationSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    discounted_price = serializers.ReadOnlyField()
    product_attributes = ProductAttributeSerializer(many=True, read_only=True)

    is_in_stock = serializers.ReadOnlyField()
    average_rating = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'product_type', 'category', 'parent_category', 'brand',
            'description', 'product_details', 'additional_information',
            'discount_type', 'discount', 'price', 'discounted_price', 'sku',
            'stock_quantity', 'product_views', 'quantity_sold', 'images',
            'rating', 'average_rating', 'tags', 'attributes', 'variations',
            'reviews', 'is_in_stock', 'is_active', 'created_at', 'updated_at','product_attributes'
        ]

    def get_attributes(self, obj):
        """Get attributes for variable products"""
        if obj.product_type != 'variable':
            return []
        return ProductAttributeSerializer(obj.attributes, many=True).data

    def get_reviews(self, obj):
        """Return approved reviews"""
        approved_reviews = obj.reviews.filter(is_approved=True)
        return ReviewSerializer(approved_reviews, many=True).data


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating products, now handling attribute
    creation/resolution.
    """
    sku = serializers.CharField(required=False, allow_blank=True, help_text="Leave blank to auto-generate")
    price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True, help_text="Price as decimal. Optional for variable products.")
    description = serializers.CharField(required=False, allow_blank=True, help_text="Product description is optional")
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, help_text="Discount amount, defaults to 0")
    
    # NEW: Accepts flexible data (IDs, or objects {name, value} for resolution)
    attributes = serializers.JSONField(
        required=False,
        help_text="List of ProductAttribute IDs or list of {name, value} objects."
    )

    product_images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'product_type', 'category', 'parent_category', 'brand',
            'description', 'product_details', 'additional_information',
            'discount_type', 'discount', 'price', 'sku', 'stock_quantity',
            'images', 'product_images', 'tags', 'attributes', 'is_active'
        ]

    def get_product_images(self, obj):
        from .models import ProductImage
        images = ProductImage.objects.filter(product=obj, is_active=True).order_by('display_order', 'created_at')
        return ProductImageSerializer(images, many=True).data

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Product name is required")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Product name must be at least 3 characters long")
        return value.strip()

    def get_product_images(self, obj):
        from .models import ProductImage
        images = ProductImage.objects.filter(product=obj, is_active=True).order_by('display_order', 'created_at')
        return ProductImageSerializer(images, many=True).data

    def validate_price(self, value):
        if value is None or value == "":
            return None
        try:
            price_value = Decimal(str(value))
            if price_value < 0:
                raise serializers.ValidationError("Price cannot be negative")
            return price_value
        except (ValueError, TypeError, InvalidOperation):
            raise serializers.ValidationError("A valid number is required")

    def validate_discount(self, value):
        """Validate discount field - defaults to 0 if empty"""
        if value is None or value == "" or value == "":
            return Decimal('0.00')
        try:
            discount_value = Decimal(str(value))
            if discount_value < 0:
                raise serializers.ValidationError("Discount cannot be negative")
            return discount_value
        except (ValueError, TypeError, InvalidOperation):
            raise serializers.ValidationError("A valid number is required")

    def validate_attributes(self, value):
        """
        FIX: Handles incoming attributes (JSON list of IDs or {name, value} objects).
        Creates ProductAttribute and AttributeValue models if necessary,
        and returns a clean list of ProductAttribute IDs.
        """
        if not value:
            return []
        
        # 1. Parse string if needed
        if isinstance(value, str):
            value = value.strip()
            if not value: return []
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return []

        if not isinstance(value, list):
            return []
            
        final_attribute_ids = []
        
        from .models import ProductAttribute, AttributeValue

        for item in value:
            if isinstance(item, int):
                # If it's already an ID, just validate existence and add it
                if ProductAttribute.objects.filter(id=item).exists():
                    final_attribute_ids.append(item)
            elif isinstance(item, dict) and 'name' in item:
                # If it's a dict, we assume it's a new/existing attribute to define
                name = item['name'].strip()
                if not name: continue

                # Get or create the ProductAttribute
                attribute, _ = ProductAttribute.objects.get_or_create(name=name, defaults={'name': name})
                final_attribute_ids.append(attribute.id)
                
                # Optionally handle AttributeValue creation
                if 'value' in item and item['value']:
                    val = item['value'].strip()
                    if val:
                        # Ensure the value exists for this attribute
                        AttributeValue.objects.get_or_create(attribute=attribute, value=val, defaults={'value': val})
        
        # Return unique IDs
        return list(set(final_attribute_ids))

    def validate_sku(self, value):
        if not value or not value.strip():
            return ""
        queryset = Product.objects.filter(sku=value.strip())
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A product with this SKU already exists")
        return value.strip().upper()

    def validate_discount(self, value):
        if value < 0:
            raise serializers.ValidationError("Discount cannot be negative")
        return value

    def validate(self, attrs):
        discount_type = attrs.get('discount_type')
        discount = attrs.get('discount')
        price = attrs.get('price')
        product_type = attrs.get('product_type', 'simple')
        stock_quantity = attrs.get('stock_quantity')

        if product_type == 'simple':
            if price is None:
                raise serializers.ValidationError({'price': 'Price is required for simple products'})
            if stock_quantity is None:
                raise serializers.ValidationError({'stock_quantity': 'Stock quantity is required for simple products'})
        
        if discount and discount > 0 and not discount_type:
            raise serializers.ValidationError({'discount_type': 'Discount type is required when discount is set'})
        if discount_type == 'percentage' and discount and discount > 100:
            raise serializers.ValidationError({'discount': 'Percentage discount cannot exceed 100%'})
        if discount_type == 'fixed' and discount and price and price is not None and discount >= price:
            raise serializers.ValidationError({'discount': 'Fixed discount cannot be greater than or equal to the price'})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        attributes_data = validated_data.pop('attributes', [])
        tags_data = validated_data.pop('tags', [])
        
        product = Product.objects.create(**validated_data)
        
        if attributes_data:
            product.attributes.set(attributes_data)
        if tags_data:
            product.tags.set(tags_data)
        
        # Update price for variable product based on minimum variation price (if any)
        if product.product_type == "variable":
            min_price = ProductVariation.objects.filter(product=product, price__isnull=False).order_by('price').values_list('price', flat=True).first()
            if min_price is not None:
                product.price = min_price
                product.save(update_fields=["price"])

        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        # Defensive: If attributes is a list, reload instance from DB to restore related manager
        if isinstance(instance.attributes, list):
            from .models import Product
            instance = Product.objects.get(pk=instance.pk)
            self.instance = instance
        
        attributes_data = validated_data.pop('attributes', None)
        tags_data = validated_data.pop('tags', None)

        # Update scalar fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update M2M fields
        if attributes_data is not None:
            # attributes_data should already be a list of IDs from validate_attributes
            if hasattr(instance, "attributes") and hasattr(instance.attributes, "set") and isinstance(attributes_data, list):
                instance.attributes.set(attributes_data)
        
        if tags_data is not None:
            if hasattr(instance, "tags") and hasattr(instance.tags, "set") and isinstance(tags_data, list):
                instance.tags.set(tags_data)
        
        # --- VARIATIONS UPDATE LOGIC ---
        variations_data = self.initial_data.get('variations', None)
        print("Variations data:", variations_data)
        if variations_data is not None:
            # Parse JSON string if necessary
            if isinstance(variations_data, str):
                try:
                    variations_data = json.loads(variations_data)
                except (json.JSONDecodeError, TypeError):
                    variations_data = []
            
            from .models import ProductVariation
            # Remove variations not present in the payload
            existing_ids = [v.get('id') for v in variations_data if v.get('id') and isinstance(v, dict)]
            ProductVariation.objects.filter(product=instance).exclude(id__in=existing_ids).delete()
            for variation in variations_data:
                if not isinstance(variation, dict):
                    continue  # Skip non-dict items
                
                var_id = variation.get('id')
                if var_id:
                    # Update existing variation
                    ProductVariation.objects.filter(id=var_id, product=instance).update(
                        sku=variation.get('sku', ''),
                        price=variation.get('price', None),
                        stock_quantity=variation.get('stock_quantity', None),
                        is_active=variation.get('is_active', True),
                        # Add other fields as needed
                    )
                else:
                    # Create new variation
                    ProductVariation.objects.create(
                        product=instance,
                        sku=variation.get('sku', ''),
                        price=variation.get('price', None),
                        stock_quantity=variation.get('stock_quantity', None),
                        is_active=variation.get('is_active', True),
                        # Add other fields as needed
                    )
        # --- END VARIATIONS UPDATE LOGIC ---

        # Update price for variable product based on minimum variation price (if any)
        if instance.product_type == "variable":
            min_price = ProductVariation.objects.filter(product=instance, price__isnull=False).order_by('price').values_list('price', flat=True).first()
            if min_price is not None:
                instance.price = min_price
                instance.save(update_fields=["price"])
            
        return instance


class ProductImageSerializer(serializers.ModelSerializer):
    image_source = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductImage
        fields = [
            'id', 'product', 'product_variation', 'image', 'image_url', 
            'alt_text', 'image_type', 'display_order', 'is_active',
            'file_size', 'width', 'height', 'image_source', 'created_at', 'updated_at'
        ]
        read_only_fields = ['file_size', 'width', 'height', 'image_source']

    def validate(self, attrs):
        """Validate that either image or image_url is provided"""
        image = attrs.get('image')
        image_url = attrs.get('image_url')
        
        if not image and not image_url:
            raise serializers.ValidationError({
                'non_field_errors': ['Either image file or image URL must be provided']
            })
        
        if image and image_url:
            raise serializers.ValidationError({
                'non_field_errors': ['Provide either image file or image URL, not both']
            })
        
        return attrs

    def validate_image_url(self, value):
        """Validate image URL format"""
        if value:
            # Basic URL validation - you might want to add more sophisticated validation
            if not (value.startswith('http://') or value.startswith('https://')):
                raise serializers.ValidationError('Image URL must start with http:// or https://')
        return value

    def validate_display_order(self, value):
        """Validate display order is non-negative"""
        if value < 0:
            raise serializers.ValidationError('Display order must be non-negative')
        return value