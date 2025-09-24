
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from .routers import router

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),  # Router URLs for ViewSets
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/', include('user_management.urls')),  # Custom auth endpoints
    path('api/orders/', include('order_management.urls')),  # Order management endpoints
    path('api/core/', include('core.urls')),  # Core functionality endpoints
    path('api/payments/', include('payments.urls')),  # Payment endpoints
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
