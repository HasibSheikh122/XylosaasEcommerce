from django.urls import path
from .views import CustomerViewSet, RegisterView, LoginView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    # লিস্ট দেখা এবং নতুন কাস্টমার তৈরি করা
    path('customers/', CustomerViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='customer-list'),

    # নির্দিষ্ট কাস্টমারের ডিটেইলস দেখা, আপডেট করা এবং ডিলিট করা
    path('customers/<int:pk>/', CustomerViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='customer-detail'),
]