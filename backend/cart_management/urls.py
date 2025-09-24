from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import CartViewSet, CartItemViewSet

# Create router for ViewSets
router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'cart-items', CartItemViewSet, basename='cart-items')

app_name = 'cart_management'

urlpatterns = [
    path('', include(router.urls)),
]