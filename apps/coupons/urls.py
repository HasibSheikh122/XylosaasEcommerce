from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CouponViewSet,
    CouponUsageViewSet,
    CouponRuleViewSet,
    CouponCategoryViewSet,
)

router = DefaultRouter()
router.register(r'categories', CouponCategoryViewSet, basename='coupon-category')
router.register(r'rules', CouponRuleViewSet, basename='coupon-rule')
router.register(r'usages', CouponUsageViewSet, basename='coupon-usage')
router.register(r'', CouponViewSet, basename='coupon')

urlpatterns = [
    # 🌟 সরাসরি ভ্যালিডেশন এন্ডপয়েন্ট (যাতে 404 না আসে)
    path('validate-coupon/', CouponViewSet.as_view({'post': 'validate_coupon'}), name='validate-coupon'),
    path('', include(router.urls)),
]