from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')

app_name = 'payments'

urlpatterns = [
    path('api/', include(router.urls)),
]