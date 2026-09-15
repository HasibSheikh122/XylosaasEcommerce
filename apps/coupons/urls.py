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
    path('', include(router.urls)),
]