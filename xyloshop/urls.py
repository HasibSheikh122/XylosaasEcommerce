from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# OpenAPI Schema View Configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Xylosaas Multi-Tenant Ecommerce API",
        default_version='v1',
        description="Complete Interactive REST API Documentation for Xylosaas Platform",
        contact=openapi.Contact(email="developer@xylosaas.com"),
        license=openapi.License(name="Private & Confidential"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # OpenAPI / Swagger Documentation URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # টেন্যান্ট API v1
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/stores/', include('apps.stores.urls')),
    path('api/v1/products/', include('apps.products.urls')),
    path('api/v1/orders/', include('apps.orders.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/customers/', include('apps.customers.urls')),
    path('api/v1/inventory/', include('apps.inventory.urls')),
    path('api/v1/shipping/', include('apps.shipping.urls')),
    path('api/v1/coupons/', include('apps.coupons.urls')),
    path('api/v1/reviews/', include('apps.reviews.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
    path('api/v1/ai/', include('apps.ai_engine.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)