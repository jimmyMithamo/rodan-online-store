from rest_framework import serializers
from .models import Cart, CartItem
from product_management.serializers import ProductListSerializer, ProductVariationSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for CartItem model"""
    product_details = ProductListSerializer(source='product', read_only=True)
    variation_details = ProductVariationSerializer(source='product_variation', read_only=True)
    unit_price = serializers.ReadOnlyField()
    subtotal = serializers.ReadOnlyField()
    product_name = serializers.ReadOnlyField()
    product_sku = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_variation', 'quantity', 'unit_price',
            'subtotal', 'product_name', 'product_sku', 'is_available',
            'product_details', 'variation_details', 'created_at', 'updated_at'
        ]
        read_only_fields = ['cart', 'created_at', 'updated_at']

    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value

    def validate(self, data):
        """Validate product and variation compatibility"""
        product = data.get('product')
        product_variation = data.get('product_variation')
        
        if product_variation and product_variation.product != product:
            raise serializers.ValidationError(
                "Product variation does not belong to the specified product"
            )
        
        # Check if product is active
        if not product.is_active:
            raise serializers.ValidationError("This product is no longer available")
        
        # Check if variation is active (if provided)
        if product_variation and not product_variation.is_active:
            raise serializers.ValidationError("This product variation is no longer available")
        
        return data


class CartItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating cart items"""
    
    class Meta:
        model = CartItem
        fields = ['product', 'product_variation', 'quantity']

    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value

    def validate(self, data):
        """Validate product and variation compatibility"""
        product = data.get('product')
        product_variation = data.get('product_variation')
        quantity = data.get('quantity', 1)
        
        if product_variation and product_variation.product != product:
            raise serializers.ValidationError(
                "Product variation does not belong to the specified product"
            )
        
        # Check if product is active
        if not product.is_active:
            raise serializers.ValidationError("This product is no longer available")
        
        # Check if variation is active (if provided)
        if product_variation and not product_variation.is_active:
            raise serializers.ValidationError("This product variation is no longer available")
        
        # Check stock availability
        if product_variation:
            available_stock = product_variation.stock_quantity
        else:
            available_stock = product.stock_quantity
        
        if available_stock < quantity:
            raise serializers.ValidationError(
                f"Only {available_stock} items available in stock"
            )
        
        return data


class CartItemUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating cart items"""
    
    class Meta:
        model = CartItem
        fields = ['quantity']

    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value

    def validate(self, data):
        """Validate stock availability for updated quantity"""
        quantity = data.get('quantity')
        instance = self.instance
        
        # Check stock availability
        if instance.product_variation:
            available_stock = instance.product_variation.stock_quantity
        else:
            available_stock = instance.product.stock_quantity
        
        if available_stock < quantity:
            raise serializers.ValidationError(
                f"Only {available_stock} items available in stock"
            )
        
        return data


class CartSerializer(serializers.ModelSerializer):
    """Serializer for Cart model"""
    items = CartItemSerializer(many=True, read_only=True)
    cart_total = serializers.ReadOnlyField()
    total_items = serializers.ReadOnlyField()
    unique_items_count = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = [
            'id', 'user', 'cart_total', 'total_items', 'unique_items_count',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart"""
    product_id = serializers.IntegerField()
    product_variation_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(default=1, min_value=1)

    def validate_product_id(self, value):
        """Validate product exists and is active"""
        from product_management.models import Product
        
        try:
            product = Product.objects.get(id=value)
            if not product.is_active:
                raise serializers.ValidationError("This product is no longer available")
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")

    def validate_product_variation_id(self, value):
        """Validate product variation exists and is active"""
        if value is None:
            return value
        
        from product_management.models import ProductVariation
        
        try:
            variation = ProductVariation.objects.get(id=value)
            if not variation.is_active:
                raise serializers.ValidationError("This product variation is no longer available")
            return value
        except ProductVariation.DoesNotExist:
            raise serializers.ValidationError("Product variation not found")

    def validate(self, data):
        """Validate product and variation compatibility"""
        product_id = data.get('product_id')
        product_variation_id = data.get('product_variation_id')
        quantity = data.get('quantity', 1)
        
        from product_management.models import Product, ProductVariation
        
        product = Product.objects.get(id=product_id)
        
        if product_variation_id:
            try:
                variation = ProductVariation.objects.get(id=product_variation_id)
                if variation.product.id != product_id:
                    raise serializers.ValidationError(
                        "Product variation does not belong to the specified product"
                    )
                # Check stock for variation
                if variation.stock_quantity < quantity:
                    raise serializers.ValidationError(
                        f"Only {variation.stock_quantity} items available in stock"
                    )
            except ProductVariation.DoesNotExist:
                raise serializers.ValidationError("Product variation not found")
        else:
            # Check stock for product
            if product.stock_quantity < quantity:
                raise serializers.ValidationError(
                    f"Only {product.stock_quantity} items available in stock"
                )
        
        return data