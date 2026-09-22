from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    MerchantTokenObtainPairView,
    UserViewSet,
    UserProfileView,
    ChangePasswordView,
)

router = DefaultRouter()
router.register(r'members', UserViewSet, basename='user-member')

urlpatterns = [
    # ১. সাধারণ ক্রেতাদের জন্য লগইন
    path('login/', CustomTokenObtainPairView.as_view(), name='auth-login'),

    # ২. মার্চেন্টদের জন্য আলাদা লগইন
    path('merchant-login/', MerchantTokenObtainPairView.as_view(), name='merchant-auth-login'),

    # টোকেন ও রেজিস্ট্রেশন
    path('token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('register/', UserViewSet.as_view({'post': 'register'}), name='auth-register'),
    path('me/', UserViewSet.as_view({'get': 'me', 'put': 'me', 'patch': 'me'}), name='auth-me'),

    # প্রোফাইল ও সিকিউরিটি
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    path('', include(router.urls)),
]