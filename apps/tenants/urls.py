from django.urls import path
from apps.tenants.views import TenantRegistrationView, MerchantStoreDetailsView

urlpatterns = [
    path('register/', TenantRegistrationView.as_view(), name='tenant-register'),
    path('my-store/', MerchantStoreDetailsView.as_view(), name='merchant-store-details'),
]