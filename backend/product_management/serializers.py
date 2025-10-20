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
    product_attributes = ProductAttributeSerializer(source='attributes', many=True, read_only=True)

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
        # Now we can safely use the ManyToMany field since the property conflict is resolved
        return ProductAttributeSerializer(obj.attributes.all(), many=True).data

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
    
    # Add product_attributes field for proper serialization in responses
    product_attributes = ProductAttributeSerializer(source='attributes', many=True, read_only=True)
    
    # Add tags field for proper serialization
    tags = TagSerializer(many=True, read_only=True)
    
    # Add variations field for proper serialization
    variations = ProductVariationSerializer(many=True, read_only=True)

    product_images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'product_type', 'category', 'parent_category', 'brand',
            'description', 'product_details', 'additional_information',
            'discount_type', 'discount', 'price', 'sku', 'stock_quantity',
            'images', 'product_images', 'tags', 'product_attributes', 'variations', 'is_active'
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

    def validate_variations(self, value):
        """
        Improved validation for variations data from frontend
        """
        if not value:
            return []
            
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return []
                
        if not isinstance(value, list):
            return []
            
        # Validate each variation structure
        for variation in value:
            if not isinstance(variation, dict):
                continue
                
            # Ensure required fields for variations
            if 'price' not in variation or variation['price'] in [None, ""]:
                raise serializers.ValidationError("Each variation must have a price")
                
            if 'stock_quantity' not in variation or variation['stock_quantity'] in [None, ""]:
                raise serializers.ValidationError("Each variation must have a stock quantity")
                
        return value

    def validate(self, attrs):
        """
        Custom validation that handles partial updates properly
        """
        # Get variations data from initial data (before it gets popped)
        variations_data = self.initial_data.get('variations')
        
        # For partial updates (like attribute association), don't require fields that already exist
        if self.instance and self.partial:
            # If this is a partial update, skip validation for fields not being updated
            pass
        else:
            # For creation or full updates, validate required fields
            if not attrs.get('name') and (not self.instance or not self.instance.name):
                raise serializers.ValidationError({'name': 'This field is required.'})
            
            if not attrs.get('category') and (not self.instance or not self.instance.category):
                raise serializers.ValidationError({'category': 'This field is required.'})
        
        # Continue with existing validation logic
        discount_type = attrs.get('discount_type')
        discount = attrs.get('discount')
        price = attrs.get('price')
        
        # For product_type, use the instance value if this is a partial update
        if self.instance and self.partial:
            product_type = attrs.get('product_type', self.instance.product_type)
        else:
            product_type = attrs.get('product_type', 'simple')
            
        stock_quantity = attrs.get('stock_quantity')

        # Only validate required fields for simple products and not during partial updates
        if product_type == 'simple' and not (self.instance and self.partial):
            if price is None and (not self.instance or self.instance.price is None):
                raise serializers.ValidationError({'price': 'Price is required for simple products'})
            if stock_quantity is None and (not self.instance or self.instance.stock_quantity is None):
                raise serializers.ValidationError({'stock_quantity': 'Stock quantity is required for simple products'})
        
        if discount and discount > 0 and not discount_type:
            raise serializers.ValidationError({'discount_type': 'Discount type is required when discount is set'})
        if discount_type == 'percentage' and discount and discount > 100:
            raise serializers.ValidationError({'discount': 'Percentage discount cannot exceed 100%'})
        if discount_type == 'fixed' and discount and price and price is not None and discount >= price:
            raise serializers.ValidationError({'discount': 'Fixed discount cannot be greater than or equal to the price'})

        # Validate variations if provided
        if variations_data and product_type == 'variable':
            try:
                if isinstance(variations_data, str):
                    variations_data = json.loads(variations_data)
                
                for i, variation in enumerate(variations_data):
                    if not isinstance(variation, dict):
                        raise serializers.ValidationError({
                            'variations': f'Variation at index {i} must be a valid object'
                        })
                    
                    # Validate required fields
                    if not variation.get('price'):
                        raise serializers.ValidationError({
                            'variations': f'Variation at index {i} must have a price'
                        })
                    
                    if variation.get('stock_quantity') in [None, ""]:
                        raise serializers.ValidationError({
                            'variations': f'Variation at index {i} must have a stock quantity'
                        })
                    
                    # Validate variations_attributes
                    variations_attrs = variation.get('variations_attributes', [])
                    if not variations_attrs:
                        raise serializers.ValidationError({
                            'variations': f'Variation at index {i} must have at least one attribute'
                        })
                    
                    for attr in variations_attrs:
                        if not attr.get('attribute_name') or not attr.get('value'):
                            raise serializers.ValidationError({
                                'variations': f'Variation at index {i} has invalid attribute data'
                            })
                            
            except (json.JSONDecodeError, TypeError) as e:
                raise serializers.ValidationError({
                    'variations': 'Invalid variations data format'
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # Get variations data from initial data before it gets popped
        variations_data = self.initial_data.get('variations', [])
        attributes_data = validated_data.pop('attributes', [])
        
        # Parse variations data if it's a string
        if isinstance(variations_data, str):
            try:
                variations_data = json.loads(variations_data)
            except (json.JSONDecodeError, TypeError):
                variations_data = []
        
        print(f"🔧 DEBUG: Creating product with {len(variations_data)} variations")
        print(f"🔧 DEBUG: Variations data: {variations_data}")
        
        product = Product.objects.create(**validated_data)
        
        if attributes_data:
            product.attributes.set(attributes_data)
            
        # Create variations if provided
        if variations_data and product.product_type == "variable":
            from .models import ProductVariation, ProductVariationValue, ProductAttribute, AttributeValue
            
            created_variations = []
            
            for i, variation_data in enumerate(variations_data):
                try:
                    print(f"🔧 DEBUG: Processing variation {i}: {variation_data}")
                    
                    # Extract variations_attributes
                    variations_attributes = variation_data.pop('variations_attributes', [])
                    
                    # Ensure required fields have defaults
                    sku = variation_data.get('sku', '')
                    price = variation_data.get('price')
                    stock_quantity = variation_data.get('stock_quantity')
                    discount = variation_data.get('discount', '0')
                    discount_type = variation_data.get('discount_type', 'percentage')
                    is_active = variation_data.get('is_active', True)
                    
                    # Convert price and stock to proper types
                    try:
                        price = Decimal(str(price)) if price else Decimal('0')
                    except (ValueError, TypeError, InvalidOperation):
                        price = Decimal('0')
                    
                    try:
                        stock_quantity = int(stock_quantity) if stock_quantity else 0
                    except (ValueError, TypeError):
                        stock_quantity = 0
                    
                    try:
                        discount = Decimal(str(discount)) if discount else Decimal('0')
                    except (ValueError, TypeError, InvalidOperation):
                        discount = Decimal('0')
                    
                    # Create the variation
                    variation = ProductVariation.objects.create(
                        product=product,
                        sku=sku,
                        price=price,
                        discount=discount,
                        discount_type=discount_type,
                        stock_quantity=stock_quantity,
                        is_active=is_active
                    )
                    
                    print(f"🔧 DEBUG: Created variation {variation.id}")
                    
                    # Handle variations_attributes
                    if variations_attributes:
                        for attr_data in variations_attributes:
                            attribute_name = attr_data.get('attribute_name', '').strip()
                            attribute_value = attr_data.get('value', '').strip()
                            
                            if attribute_name and attribute_value:
                                print(f"🔧 DEBUG: Creating attribute {attribute_name} = {attribute_value}")
                                
                                # Find or create the ProductAttribute
                                attribute, created = ProductAttribute.objects.get_or_create(
                                    name=attribute_name,
                                    defaults={'name': attribute_name}
                                )
                                
                                if created:
                                    print(f"🔧 DEBUG: Created new attribute: {attribute_name}")
                                
                                # Find or create the AttributeValue
                                attribute_value_obj, created = AttributeValue.objects.get_or_create(
                                    attribute=attribute,
                                    value=attribute_value,
                                    defaults={'value': attribute_value}
                                )
                                
                                if created:
                                    print(f"🔧 DEBUG: Created new attribute value: {attribute_value}")
                                
                                # Create the ProductVariationValue
                                ProductVariationValue.objects.create(
                                    product_variation=variation,
                                    attribute_value=attribute_value_obj
                                )
                                
                                print(f"🔧 DEBUG: Created ProductVariationValue for variation {variation.id}")
                    
                    created_variations.append(variation)
                    
                except Exception as e:
                    print(f"❌ ERROR: Failed to create variation {i}: {str(e)}")
                    import traceback
                    print(f"❌ ERROR: Traceback: {traceback.format_exc()}")
                    # Continue with other variations even if one fails
                    continue
            
            print(f"🔧 DEBUG: Successfully created {len(created_variations)} variations")
            
            # Auto-associate attributes used in variations with the product
            if created_variations:
                self._auto_associate_attributes(product, created_variations)
        
        return product

    def _auto_associate_attributes(self, product, variations):
        """Automatically associate attributes used in variations with the product"""
        from .models import ProductAttribute
        
        attribute_ids = set()
        
        for variation in variations:
            for variation_value in variation.productvariationvalue_set.all():
                attribute_ids.add(variation_value.attribute_value.attribute.id)
        
        if attribute_ids:
            product.attributes.add(*attribute_ids)
            print(f"🔧 DEBUG: Auto-associated {len(attribute_ids)} attributes with product")

    @transaction.atomic
    def update(self, instance, validated_data):
        # Defensive: If attributes is a list, reload instance from DB to restore related manager
        if isinstance(instance.attributes, list):
            from .models import Product
            instance = Product.objects.get(pk=instance.pk)
            self.instance = instance
        
        # Get variations data from initial data before it gets popped
        variations_data = self.initial_data.get('variations')
        attributes_data = validated_data.pop('attributes', None)

        # Update scalar fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update M2M fields
        if attributes_data is not None:
            # attributes_data should already be a list of IDs from validate_attributes
            if hasattr(instance, "attributes") and hasattr(instance.attributes, "set") and isinstance(attributes_data, list):
                instance.attributes.set(attributes_data)
        
        # 🔧 BACKEND REPAIR: Handle missing product-level attributes for variable products
        if (instance.product_type == 'variable' and 
            (not attributes_data or len(attributes_data) == 0)):
            
            # Check if we have product_attributes data in the request
            product_attributes_data = self.initial_data.get('product_attributes', [])
            if product_attributes_data:
                print("🔧 BACKEND REPAIR: Detecting missing product attributes, attempting repair...")
                
                # Extract attribute names and find/create the ProductAttribute records
                attribute_ids_to_associate = []
                
                for attr_data in product_attributes_data:
                    if isinstance(attr_data, dict) and 'name' in attr_data:
                        attr_name = attr_data['name']
                        try:
                            # Find or create the ProductAttribute
                            from .models import ProductAttribute
                            product_attribute, created = ProductAttribute.objects.get_or_create(name=attr_name)
                            attribute_ids_to_associate.append(product_attribute.id)
                            
                            if created:
                                print(f"🔧 BACKEND REPAIR: Created ProductAttribute: {attr_name}")
                            else:
                                print(f"🔧 BACKEND REPAIR: Found existing ProductAttribute: {attr_name}")
                                
                        except Exception as e:
                            print(f"🔧 BACKEND REPAIR: Error processing attribute {attr_name}: {e}")
                
                # Associate the attributes with the product
                if attribute_ids_to_associate:
                    instance.attributes.set(attribute_ids_to_associate)
                    print(f"🔧 BACKEND REPAIR: Associated {len(attribute_ids_to_associate)} attributes with product")
        
        # --- VARIATIONS UPDATE LOGIC ---
        if variations_data is not None:
            # Parse JSON string if necessary
            if isinstance(variations_data, str):
                try:
                    variations_data = json.loads(variations_data)
                except (json.JSONDecodeError, TypeError):
                    variations_data = []
            
            print(f"🔧 DEBUG: Updating product with {len(variations_data)} variations")
            print(f"🔧 DEBUG: Variations data: {variations_data}")
            
            from .models import ProductVariation, ProductVariationValue, ProductAttribute, AttributeValue
            
            # Remove variations not present in the payload
            existing_ids = [v.get('id') for v in variations_data if v.get('id') and isinstance(v, dict)]
            ProductVariation.objects.filter(product=instance).exclude(id__in=existing_ids).delete()
            
            created_variations = []
            
            for variation in variations_data:
                if not isinstance(variation, dict):
                    continue
                
                var_id = variation.get('id')
                variations_attributes = variation.get('variations_attributes', [])
                
                if var_id:
                    # Update existing variation
                    variation_obj = ProductVariation.objects.filter(id=var_id, product=instance).first()
                    if variation_obj:
                        variation_obj.sku = variation.get('sku', '')
                        
                        # Convert price and stock to proper types
                        try:
                            price = Decimal(str(variation.get('price'))) if variation.get('price') else Decimal('0')
                            variation_obj.price = price
                        except (ValueError, TypeError, InvalidOperation):
                            variation_obj.price = Decimal('0')
                        
                        try:
                            stock_quantity = int(variation.get('stock_quantity')) if variation.get('stock_quantity') else 0
                            variation_obj.stock_quantity = stock_quantity
                        except (ValueError, TypeError):
                            variation_obj.stock_quantity = 0
                        
                        try:
                            discount = Decimal(str(variation.get('discount'))) if variation.get('discount') else Decimal('0')
                            variation_obj.discount = discount
                        except (ValueError, TypeError, InvalidOperation):
                            variation_obj.discount = Decimal('0')
                        
                        variation_obj.discount_type = variation.get('discount_type', 'percentage')
                        variation_obj.is_active = variation.get('is_active', True)
                        variation_obj.save()
                        
                        # Process variations_attributes for existing variation
                        self._update_variation_attributes(variation_obj, variations_attributes)
                        created_variations.append(variation_obj)
                else:
                    # Create new variation
                    try:
                        # Convert price and stock to proper types
                        price = Decimal(str(variation.get('price'))) if variation.get('price') else Decimal('0')
                        stock_quantity = int(variation.get('stock_quantity')) if variation.get('stock_quantity') else 0
                        discount = Decimal(str(variation.get('discount'))) if variation.get('discount') else Decimal('0')
                        
                        variation_obj = ProductVariation.objects.create(
                            product=instance,
                            sku=variation.get('sku', ''),
                            price=price,
                            discount=discount,
                            discount_type=variation.get('discount_type', 'percentage'),
                            stock_quantity=stock_quantity,
                            is_active=variation.get('is_active', True),
                        )
                        
                        print("Created new variation:", variation)
                        
                        # Process variations_attributes for new variation
                        self._update_variation_attributes(variation_obj, variations_attributes)
                        created_variations.append(variation_obj)
                    except Exception as e:
                        print(f"❌ ERROR: Failed to create new variation: {str(e)}")
                        import traceback
                        print(f"❌ ERROR: Traceback: {traceback.format_exc()}")
            
            # Auto-associate attributes used in variations with the product
            if created_variations:
                self._auto_associate_attributes(instance, created_variations)
        # --- END VARIATIONS UPDATE LOGIC ---

        # Update price for variable product based on minimum variation price (if any)
        if instance.product_type == "variable":
            from .models import ProductVariation  # Local import for safety
            min_price = ProductVariation.objects.filter(product=instance, price__isnull=False).order_by('price').values_list('price', flat=True).first()
            if min_price is not None:
                instance.price = min_price
                instance.save(update_fields=["price"])
            
        return instance

    def _update_variation_attributes(self, variation_obj, variations_attributes):
        """Helper method to update ProductVariationValue records for a variation"""
        from .models import ProductVariationValue, ProductAttribute, AttributeValue
        
        # Clear existing variation values
        ProductVariationValue.objects.filter(product_variation=variation_obj).delete()
        
        # Create new variation values
        for attr_data in variations_attributes:
            if not isinstance(attr_data, dict):
                continue
                
            attr_name = attr_data.get('attribute_name')
            attr_value = attr_data.get('value')
            
            if not attr_name or not attr_value:
                continue
                
            try:
                # Find or create the ProductAttribute
                product_attribute, _ = ProductAttribute.objects.get_or_create(name=attr_name)
                
                # Find or create the AttributeValue
                attribute_value, _ = AttributeValue.objects.get_or_create(
                    attribute=product_attribute,
                    value=attr_value
                )
                
                # Create the ProductVariationValue
                ProductVariationValue.objects.create(
                    product_variation=variation_obj,
                    attribute_value=attribute_value
                )
                
                print(f"Created ProductVariationValue: {variation_obj.sku} -> {attr_name}: {attr_value}")
                
            except Exception as e:
                print(f"Error creating variation attribute {attr_name}={attr_value}: {e}")
                import traceback
                print(f"Error traceback: {traceback.format_exc()}")
                continue

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