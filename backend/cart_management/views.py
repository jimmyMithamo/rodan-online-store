from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.shortcuts import get_object_or_404

from .models import Cart, CartItem
from .serializers import (
    CartSerializer, CartItemSerializer, CartItemCreateSerializer,
    CartItemUpdateSerializer, AddToCartSerializer
)
from product_management.models import Product, ProductVariation


class CartViewSet(viewsets.ModelViewSet):
    """ViewSet for Cart model"""
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return cart for current user"""
        return Cart.objects.filter(user=self.request.user).prefetch_related('items__product', 'items__product_variation')

    def get_object(self):
        """Get or create cart for current user"""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def list(self, request, *args, **kwargs):
        """Get current user's cart"""
        cart = self.get_object()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Get current user's cart"""
        return self.list(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add item to cart"""
        serializer = AddToCartSerializer(data=request.data)
        if serializer.is_valid():
            cart = self.get_object()
            
            # Get product and variation
            product = get_object_or_404(Product, id=serializer.validated_data['product_id'])
            product_variation = None
            if serializer.validated_data.get('product_variation_id'):
                product_variation = get_object_or_404(
                    ProductVariation, 
                    id=serializer.validated_data['product_variation_id']
                )
            
            quantity = serializer.validated_data['quantity']
            
            # Add item to cart
            cart_item = cart.add_item(product, product_variation, quantity)
            
            # Return updated cart
            cart_serializer = CartSerializer(cart)
            return Response({
                'message': 'Item added to cart successfully',
                'cart': cart_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """Remove item from cart"""
        product_id = request.data.get('product_id')
        product_variation_id = request.data.get('product_variation_id')
        
        if not product_id:
            return Response(
                {'error': 'product_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cart = self.get_object()
        product = get_object_or_404(Product, id=product_id)
        product_variation = None
        
        if product_variation_id:
            product_variation = get_object_or_404(ProductVariation, id=product_variation_id)
        
        # Remove item from cart
        removed = cart.remove_item(product, product_variation)
        
        if removed:
            cart_serializer = CartSerializer(cart)
            return Response({
                'message': 'Item removed from cart successfully',
                'cart': cart_serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Item not found in cart'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def update_item(self, request):
        """Update item quantity in cart"""
        product_id = request.data.get('product_id')
        product_variation_id = request.data.get('product_variation_id')
        quantity = request.data.get('quantity')
        
        if not product_id or quantity is None:
            return Response(
                {'error': 'product_id and quantity are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if quantity < 0:
            return Response(
                {'error': 'Quantity must be non-negative'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cart = self.get_object()
        product = get_object_or_404(Product, id=product_id)
        product_variation = None
        
        if product_variation_id:
            product_variation = get_object_or_404(ProductVariation, id=product_variation_id)
        
        # Update item quantity
        cart_item = cart.update_item_quantity(product, product_variation, quantity)
        
        cart_serializer = CartSerializer(cart)
        if quantity == 0:
            message = 'Item removed from cart successfully'
        else:
            message = 'Item quantity updated successfully'
        
        return Response({
            'message': message,
            'cart': cart_serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear all items from cart"""
        cart = self.get_object()
        cart.clear_cart()
        
        cart_serializer = CartSerializer(cart)
        return Response({
            'message': 'Cart cleared successfully',
            'cart': cart_serializer.data
        }, status=status.HTTP_200_OK)


class CartItemViewSet(viewsets.ModelViewSet):
    """ViewSet for CartItem model"""
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['product', 'product_variation']
    search_fields = ['product__name', 'product__sku']
    ordering_fields = ['created_at', 'quantity', 'subtotal']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return cart items for current user's cart"""
        try:
            cart = Cart.objects.get(user=self.request.user)
            return CartItem.objects.filter(cart=cart).select_related('product', 'product_variation')
        except Cart.DoesNotExist:
            return CartItem.objects.none()

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return CartItemCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CartItemUpdateSerializer
        return CartItemSerializer

    def perform_create(self, serializer):
        """Create cart item for current user's cart"""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        
        # Check if item already exists
        product = serializer.validated_data['product']
        product_variation = serializer.validated_data.get('product_variation')
        quantity = serializer.validated_data['quantity']
        
        try:
            # If item exists, update quantity
            existing_item = CartItem.objects.get(
                cart=cart,
                product=product,
                product_variation=product_variation
            )
            existing_item.quantity += quantity
            existing_item.save()
            
            # Update the serializer instance to return the updated item
            serializer.instance = existing_item
        except CartItem.DoesNotExist:
            # Create new item
            serializer.save(cart=cart)

    def perform_update(self, serializer):
        """Ensure user can only update their own cart items"""
        if serializer.instance.cart.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only update your own cart items")
        serializer.save()

    def perform_destroy(self, instance):
        """Ensure user can only delete their own cart items"""
        if instance.cart.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own cart items")
        instance.delete()
