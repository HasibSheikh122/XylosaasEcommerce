from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # ⚠️ পরিবর্তন: লগইন এবং টোকেন রিফ্রেশ পাথ দুটিকে রাউটারের উপরে নিয়ে আসা হয়েছে
    # এর ফলে জ্যাঙ্গো 'users/login/' রিকোয়েস্ট পেলে রাউটারে যাওয়ার আগেই টোকেন ভিউ চালু করবে।
    path('users/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Router থাকবে সবার নিচে
    path('', include(router.urls)),
]