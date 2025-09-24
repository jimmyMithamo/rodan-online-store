from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderViewSet, OrderItemViewSet, CouponViewSet, CouponUsageViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='orderitem')
router.register(r'coupons', CouponViewSet, basename='coupon')
router.register(r'coupon-usage', CouponUsageViewSet, basename='couponusage')

app_name = 'order_management'

urlpatterns = [
    path('api/', include(router.urls)),
]