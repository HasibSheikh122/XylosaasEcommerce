from django.urls import path
from .views import PlanViewSet, SubscriptionViewSet

urlpatterns = [
    # ----------------------------------------------------
    # ১. প্ল্যান (Plans) এন্ডপয়েন্টসমূহ
    # ----------------------------------------------------
    path('plans/', PlanViewSet.as_view({'get': 'list'}), name='plan-list'),
    path('plans/<int:pk>/', PlanViewSet.as_view({'get': 'retrieve'}), name='plan-detail'),

    # ----------------------------------------------------
    # ২. সাবস্ক্রিপশন (Subscriptions) মেইন এন্ডপয়েন্টসমূহ
    # ----------------------------------------------------
    path('subscriptions/', SubscriptionViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='subscription-list-create'),
    
    path('subscriptions/<int:pk>/', SubscriptionViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='subscription-detail'),

    # ----------------------------------------------------
    # ৩. সাবস্ক্রিপশন কাস্টম অ্যাকশন এন্ডপয়েন্টসমূহ (Explicit Path System)
    # ----------------------------------------------------
    path('subscriptions/<int:pk>/cancel/', SubscriptionViewSet.as_view({'post': 'cancel_subscription'}), name='subscription-cancel'),
    path('subscriptions/<int:pk>/upgrade-downgrade/', SubscriptionViewSet.as_view({'post': 'upgrade_downgrade'}), name='subscription-upgrade-downgrade'),
]