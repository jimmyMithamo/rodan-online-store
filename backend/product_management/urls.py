from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, TagViewSet, ProductAttributeViewSet, 
    AttributeValueViewSet, ProductViewSet, ProductVariationViewSet, 
    ReviewViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'attributes', ProductAttributeViewSet, basename='productattribute')
router.register(r'attribute-values', AttributeValueViewSet, basename='attributevalue')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'variations', ProductVariationViewSet, basename='productvariation')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]