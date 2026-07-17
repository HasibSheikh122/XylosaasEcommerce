from django.urls import path
from .views import (
    PaymentGatewayViewSet, PaymentTransactionViewSet,
    PaymentSubscriptionViewSet, PaymentRefundViewSet, PaymentLogViewSet
)

app_name = 'payments'

urlpatterns = [
    # Payment Gateway URLs
    path('gateways/', PaymentGatewayViewSet.as_view({
        'get': 'list', 
        'post': 'create'
    }), name='gateway-list'),
    
    path('gateways/<int:pk>/', PaymentGatewayViewSet.as_view({
        'get': 'retrieve', 
        'put': 'update', 
        'patch': 'partial_update', 
        'delete': 'destroy'
    }), name='gateway-detail'),

    # Payment Transaction URLs
    path('transactions/', PaymentTransactionViewSet.as_view({
        'get': 'list', 
        'post': 'create'
    }), name='transaction-list'),
    
    path('transactions/<int:pk>/', PaymentTransactionViewSet.as_view({
        'get': 'retrieve', 
        'patch': 'partial_update'
    }), name='transaction-detail'),

    # Payment Subscription URLs
    path('subscriptions/', PaymentSubscriptionViewSet.as_view({
        'get': 'list', 
        'post': 'create'
    }), name='subscription-list'),
    
    path('subscriptions/<int:pk>/', PaymentSubscriptionViewSet.as_view({
        'get': 'retrieve', 
        'put': 'update', 
        'patch': 'partial_update', 
        'delete': 'destroy'
    }), name='subscription-detail'),

    # Payment Refund URLs
    path('refunds/', PaymentRefundViewSet.as_view({
        'get': 'list', 
        'post': 'create'
    }), name='refund-list'),
    
    path('refunds/<int:pk>/', PaymentRefundViewSet.as_view({
        'get': 'retrieve', 
        'put': 'update', 
        'patch': 'partial_update', 
        'delete': 'destroy'
    }), name='refund-detail'),

    # Payment Log URLs (Read Only)
    path('logs/', PaymentLogViewSet.as_view({
        'get': 'list'
    }), name='log-list'),
    
    path('logs/<int:pk>/', PaymentLogViewSet.as_view({
        'get': 'retrieve'
    }), name='log-detail'),
]