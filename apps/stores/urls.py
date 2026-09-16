from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StoreSettingsViewSet,
    StoreStaffViewSet,
    StoreCategoryViewSet,
    StorePageViewSet,
    StoreNotificationViewSet,
)

router = DefaultRouter()
router.register(r'staff', StoreStaffViewSet, basename='store-staff')
router.register(r'categories', StoreCategoryViewSet, basename='store-category')
router.register(r'pages', StorePageViewSet, basename='store-page')
router.register(r'notifications', StoreNotificationViewSet, basename='store-notification')

urlpatterns = [
    # স্টোর সেটিংসের একক এন্ডপয়েন্ট (GET: ভিউ, PUT/PATCH: আপডেট)
    path('settings/', StoreSettingsViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'update'}), name='store-settings'),
    path('', include(router.urls)),
]