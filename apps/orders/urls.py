# apps/orders/urls.py

from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # ==========================================
    # 🛒 CART URLs
    # ==========================================
    
    # সব কার্টের লিস্ট দেখা এবং নতুন কার্ট তৈরি করা
    path('carts/', views.CartViewSet.as_view({'get': 'list', 'post': 'create'}), name='cart-list'),
    
    # নির্দিষ্ট কার্টের বিস্তারিত দেখা, আপডেট বা ডিলিট করা
    path('carts/<str:cart_token>/', views.CartViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='cart-detail'),
    
    # কার্টে আইটেম যোগ করা
    path('carts/<str:cart_token>/add_item/', views.CartViewSet.as_view({'post': 'add_item'}), name='cart-add-item'),
    
    # কার্ট থেকে আইটেম মুছে ফেলা (যদি আপনি এই মেথডটি views.py তে অ্যাড করে থাকেন)
    path('carts/<str:cart_token>/remove_item/', views.CartViewSet.as_view({'post': 'remove_item'}), name='cart-remove-item'),
    
    # কুপন অ্যাপ্লাই করা
    path('carts/<str:cart_token>/apply_coupon/', views.CartViewSet.as_view({'post': 'apply_coupon'}), name='cart-apply-coupon'),


    # ==========================================
    # 📦 CHECKOUT URLs
    # ==========================================
    
    # চেকআউটের লিস্ট দেখা এবং নতুন চেকআউট শুরু করা
    path('checkouts/', views.CheckoutViewSet.as_view({'get': 'list', 'post': 'create'}), name='checkout-list'),
    
    # নির্দিষ্ট চেকআউটের বিস্তারিত দেখা
    path('checkouts/<int:pk>/', views.CheckoutViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update'
    }), name='checkout-detail'),
    
    # চেকআউট সম্পন্ন করা (অর্ডার তৈরি করা)
    path('checkouts/<int:pk>/complete/', views.CheckoutViewSet.as_view({'post': 'complete'}), name='checkout-complete'),


    # ==========================================
    # 📝 ORDER URLs
    # ==========================================
    
    # অর্ডারের লিস্ট দেখা
    path('orders/', views.OrderViewSet.as_view({'get': 'list'}), name='order-list'),
    
    # নির্দিষ্ট অর্ডারের বিস্তারিত দেখা
    path('orders/<str:order_number>/', views.OrderViewSet.as_view({'get': 'retrieve'}), name='order-detail'),
]