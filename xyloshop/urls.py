from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

# পাবলিক স্কিমার জন্য ইউআরএল (যা সব টেন্যান্টের জন্য কমন)
public_patterns = [
    path('admin/', admin.site.urls),
    # এখানে কেবল গ্লোবাল অ্যাপগুলো রাখুন
]

# টেন্যান্ট স্কিমার জন্য ইউআরএল (যা প্রতিটি স্টোরের জন্য আলাদা)
tenant_patterns = [
    path('api/', include('apps.users.urls')),
    path('api/stores/', include('apps.stores.urls')),
    path('api/', include('apps.products.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/customers/', include('apps.customers.urls')),
]

urlpatterns = public_patterns + tenant_patterns

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)