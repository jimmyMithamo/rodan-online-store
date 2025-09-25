from rest_framework import serializers
from .models import (
    Banner, Category, Tag, Brand, ProductAttribute, AttributeValue, 
    Product, ProductVariation, ProductVariationValue, Review, ProductImage
)

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
    display_attributes = serializers.ReadOnlyField()
    effective_images = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    sku = serializers.CharField(required=False, allow_blank=True, help_text="Leave blank to auto-generate")
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariation
        fields = [
            'id', 'product', 'sku', 'price', 'discounted_price', 'stock_quantity', 'images',
            'variations_attributes', 'display_attributes', 'effective_images',
            'is_in_stock', 'is_active', 'created_at', 'updated_at'
        ]
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
            'reviews', 'is_in_stock', 'is_active', 'created_at', 'updated_at'
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
    """Serializer for creating and updating products"""
    sku = serializers.CharField(required=False, allow_blank=True, help_text="Leave blank to auto-generate")
    price = serializers.CharField(required=False, allow_blank=True, help_text="Price as string, will be converted to decimal. Optional for variable products.")
    attributes = serializers.CharField(required=False, allow_blank=True, help_text="JSON string or list of attribute IDs")
    product_images = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'product_type', 'category', 'parent_category', 'brand',
            'description', 'product_details', 'additional_information',
            'discount_type', 'discount', 'price', 'sku', 'stock_quantity',
            'images', 'product_images', 'tags', 'attributes', 'is_active'
        ]

    def validate_name(self, value):
        """Validate product name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Product name is required")
        
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Product name must be at least 3 characters long")
        
        return value.strip()

    def get_product_images(self, obj):
        """Return full ProductImage objects"""
        from .models import ProductImage
        images = ProductImage.objects.filter(product=obj, is_active=True).order_by('display_order', 'created_at')
        return ProductImageSerializer(images, many=True).data

    def validate_price(self, value):
        """Validate price field - convert string to decimal"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"🔧 DEBUG: validate_price called with value: {value} (type: {type(value)})")
        
        # Allow None/empty for variable products since they get pricing from variations
        if value is None or value == "":
            logger.debug("🔧 DEBUG: Price is None or empty, returning None")
            return None
        
        try:
            from decimal import Decimal, InvalidOperation
            price_value = Decimal(str(value))
            logger.debug(f"🔧 DEBUG: Converted price to Decimal: {price_value}")
            if price_value < 0:
                raise serializers.ValidationError("Price cannot be negative")
            return price_value
        except (ValueError, TypeError, InvalidOperation) as e:
            logger.debug(f"🔧 DEBUG: Price conversion failed: {e}")
            raise serializers.ValidationError("A valid number is required")

    def validate_attributes(self, value):
        """Validate attributes field - handle both IDs and JSON strings"""
        if not value or value.strip() == "":
            return []
        
        # If it's a string (JSON), try to parse it
        if isinstance(value, str):
            try:
                import json
                parsed_value = json.loads(value)
                
                # Handle different frontend formats
                if isinstance(parsed_value, list):
                    # If it's an empty list, return empty list
                    if not parsed_value:
                        return []
                    
                    # Check if it's a list of attribute IDs (integers)
                    if all(isinstance(item, int) for item in parsed_value):
                        return parsed_value
                    
                    # Check if it's the new format with {name: "", value: ""} objects
                    if isinstance(parsed_value[0], dict) and 'name' in parsed_value[0]:
                        # Convert to attribute IDs if needed - for now, return empty list
                        return []
                
                return []
            except (json.JSONDecodeError, KeyError, IndexError):
                return []
        
        # If it's already a list, validate it
        if isinstance(value, list):
            return value
        
        return []

    def validate_sku(self, value):
        """Validate SKU uniqueness only if provided"""
        # If SKU is not provided or is blank, it will be auto-generated by the model
        if not value or not value.strip():
            return ""  # Return empty string for auto-generation
        
        # Check uniqueness excluding current instance
        queryset = Product.objects.filter(sku=value.strip())
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("A product with this SKU already exists")
        
        return value.strip().upper()

    def validate_discount(self, value):
        """Validate discount"""
        if value < 0:
            raise serializers.ValidationError("Discount cannot be negative")
        return value

    def validate(self, attrs):
        """Cross-field validation"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"🔧 DEBUG: validate() called with attrs: {attrs}")
        
        discount_type = attrs.get('discount_type')
        discount = attrs.get('discount')
        price = attrs.get('price')
        product_type = attrs.get('product_type', 'simple')
        stock_quantity = attrs.get('stock_quantity')

        logger.debug(f"🔧 DEBUG: product_type: {product_type}")
        logger.debug(f"🔧 DEBUG: price: {price}")
        logger.debug(f"🔧 DEBUG: stock_quantity: {stock_quantity}")

        # For simple products, price and stock_quantity are required
        if product_type == 'simple':
            logger.debug("🔧 DEBUG: Validating simple product requirements")
            if price is None:
                logger.debug("🔧 DEBUG: Price is None for simple product - validation error")
                raise serializers.ValidationError({
                    'price': 'Price is required for simple products'
                })
            if stock_quantity is None:
                logger.debug("🔧 DEBUG: Stock quantity is None for simple product - validation error")
                raise serializers.ValidationError({
                    'stock_quantity': 'Stock quantity is required for simple products'
                })
        else:
            logger.debug("🔧 DEBUG: Variable product - price and stock_quantity not required")

        # If discount is set, discount_type is required
        if discount and discount > 0 and not discount_type:
            raise serializers.ValidationError({
                'discount_type': 'Discount type is required when discount is set'
            })

        # Validate percentage discount
        if discount_type == 'percentage' and discount and discount > 100:
            raise serializers.ValidationError({
                'discount': 'Percentage discount cannot exceed 100%'
            })

        # Validate fixed discount - only for products with price
        if discount_type == 'fixed' and discount and price and discount >= price:
            raise serializers.ValidationError({
                'discount': 'Fixed discount cannot be greater than or equal to the price'
            })

        logger.debug("🔧 DEBUG: Cross-field validation passed")
        return attrs

    def create(self, validated_data):
        """Handle product creation with attributes and many-to-many fields"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Extract many-to-many fields from validated data
        attributes_data = validated_data.pop('attributes', [])
        tags_data = validated_data.pop('tags', [])
        
        logger.debug(f"🔧 DEBUG: Create method - attributes_data: {attributes_data}")
        logger.debug(f"🔧 DEBUG: Create method - tags_data: {tags_data}")
        logger.debug(f"🔧 DEBUG: Create method - remaining validated_data: {validated_data}")
        
        # Create the product
        product = Product.objects.create(**validated_data)
        
        # Set many-to-many fields if any
        if attributes_data:
            logger.debug(f"🔧 DEBUG: Setting attributes: {attributes_data}")
            product.attributes.set(attributes_data)
            
        if tags_data:
            logger.debug(f"🔧 DEBUG: Setting tags: {tags_data}")
            product.tags.set(tags_data)
        
        return product

    def update(self, instance, validated_data):
        """Handle product update with attributes and many-to-many fields"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Extract many-to-many fields from validated data
        attributes_data = validated_data.pop('attributes', None)
        tags_data = validated_data.pop('tags', None)
        
        logger.debug(f"🔧 DEBUG: Update method - attributes_data: {attributes_data}")
        logger.debug(f"🔧 DEBUG: Update method - tags_data: {tags_data}")
        logger.debug(f"🔧 DEBUG: Update method - remaining validated_data: {validated_data}")
        
        # Update the product fields (excluding many-to-many fields)
        for attr, value in validated_data.items():
            logger.debug(f"🔧 DEBUG: Setting {attr} = {value}")
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update many-to-many fields if provided
        if attributes_data is not None:
            logger.debug(f"🔧 DEBUG: Setting attributes: {attributes_data}")
            instance.attributes.set(attributes_data)
            
        if tags_data is not None:
            logger.debug(f"🔧 DEBUG: Setting tags: {tags_data}")
            instance.tags.set(tags_data)
        
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