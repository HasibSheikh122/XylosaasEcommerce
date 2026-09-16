from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentGatewayViewSet,
    PaymentTransactionViewSet,
    PaymentRefundViewSet,
    PaymentSubscriptionViewSet,
    PaymentLogViewSet,
)

router = DefaultRouter()
router.register(r'gateways', PaymentGatewayViewSet, basename='payment-gateway')
router.register(r'transactions', PaymentTransactionViewSet, basename='payment-transaction')
router.register(r'refunds', PaymentRefundViewSet, basename='payment-refund')
router.register(r'subscriptions', PaymentSubscriptionViewSet, basename='payment-subscription')
router.register(r'logs', PaymentLogViewSet, basename='payment-log')

urlpatterns = [
    path('', include(router.urls)),
]