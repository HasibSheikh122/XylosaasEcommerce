from django.urls import path
from .views import (
    StoreSettingsViewSet, 
    StoreCategoryViewSet
)

urlpatterns = [
    # --- Category Endpoints ---
    path('categories/', StoreCategoryViewSet.as_view({
        'get': 'list', 
        'post': 'create'
    }), name='category-list'),
    
    path('categories/<int:pk>/', StoreCategoryViewSet.as_view({
        'get': 'retrieve', 
        'put': 'update', 
        'patch': 'partial_update', 
        'delete': 'destroy'
    }), name='category-detail'),

    # --- Store Settings Endpoints ---
    # সেটিংস গেট এবং প্যাচ করার জন্য
    path('settings/', StoreSettingsViewSet.as_view({
        'get': 'retrieve', 
        'patch': 'partial_update'
    }), name='store-settings'),
    
    # ব্র্যান্ডিং আপডেটের কাস্টম অ্যাকশন
    path('settings/branding/', StoreSettingsViewSet.as_view({
        'patch': 'update_branding'
    }), name='store-settings-branding'),
]