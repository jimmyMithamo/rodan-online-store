from rest_framework.routers import DefaultRouter
from user_management.views import UserViewSet, ShippingAddressViewSet
from product_management.views import (
    CategoryViewSet, TagViewSet, BrandViewSet, ProductAttributeViewSet, 
    AttributeValueViewSet, ProductViewSet, ProductVariationViewSet, 
    ReviewViewSet, ProductImageViewSet
)
from order_management.views import (
    OrderViewSet, OrderItemViewSet, CouponViewSet, CouponUsageViewSet
)
from payments.views import PaymentViewSet
from core.views import AuditLogViewSet
from cart_management.views import CartViewSet, CartItemViewSet

# Create a main router for all apps
router = DefaultRouter()

# Register User Management ViewSets
router.register(r'users', UserViewSet)
router.register(r'shipping-addresses', ShippingAddressViewSet, basename='shippingaddress')

# Register Product Management ViewSets
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'attributes', ProductAttributeViewSet, basename='productattribute')
router.register(r'attribute-values', AttributeValueViewSet, basename='attributevalue')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'variations', ProductVariationViewSet, basename='productvariation')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'product-images', ProductImageViewSet, basename='productimage')

# Register Order Management ViewSets
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='orderitem')
router.register(r'coupons', CouponViewSet, basename='coupon')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'coupon-usage', CouponUsageViewSet, basename='couponusage')
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')

# Register Cart Management ViewSets
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'cart-items', CartItemViewSet, basename='cartitem')