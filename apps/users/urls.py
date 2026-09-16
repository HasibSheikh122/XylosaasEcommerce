from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserViewSet, CustomTokenObtainPairView

router = DefaultRouter()
router.register(r'members', UserViewSet, basename='user-member')

urlpatterns = [
    # Auth & JWT Endpoints
    path('login/', CustomTokenObtainPairView.as_view(), name='auth-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('register/', UserViewSet.as_view({'post': 'register'}), name='auth-register'),
    path('me/', UserViewSet.as_view({'get': 'me', 'put': 'me', 'patch': 'me'}), name='auth-me'),
    path('change-password/', UserViewSet.as_view({'post': 'change_password'}), name='auth-change-password'),

    # Staff / Members Management
    path('', include(router.urls)),
]