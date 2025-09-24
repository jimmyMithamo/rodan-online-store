from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')

app_name = 'core'

urlpatterns = [
    path('api/', include(router.urls)),
]