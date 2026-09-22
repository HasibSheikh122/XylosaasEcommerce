from django.urls import path
from apps.tenants.views import StoreRegistrationView, TenantRegistrationView, MerchantStoreDetailsView

urlpatterns = [
    path('register-store/', StoreRegistrationView.as_view(), name='register-store'),
    path('register/', TenantRegistrationView.as_view(), name='tenant-register'),
    path('my-store/', MerchantStoreDetailsView.as_view(), name='merchant-store-details'),
]