from rest_framework import viewsets, permissions
from .models import (
    PaymentGateway, PaymentTransaction, 
    PaymentSubscription, PaymentRefund, PaymentLog
)
from .serializers import (
    PaymentGatewaySerializer, PaymentTransactionSerializer,
    PaymentSubscriptionSerializer, PaymentRefundSerializer, PaymentLogSerializer
)

class BaseTenantViewSet(viewsets.ModelViewSet):
    """
    এটি একটি কাস্টম ViewSet যা নিশ্চিত করবে যে ইউজার শুধু তার Tenant-এর ডেটাই দেখবে।
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # ইউজারের টেন্যান্ট অনুযায়ী ডেটা ফিল্টার করা
        return self.queryset.filter(tenant=self.request.user.tenant)

    def perform_create(self, serializer):
        # নতুন রেকর্ড তৈরির সময় স্বয়ংক্রিয়ভাবে ইউজারের টেন্যান্ট সেট করে দেওয়া
        serializer.save(tenant=self.request.user.tenant)


class PaymentGatewayViewSet(BaseTenantViewSet):
    queryset = PaymentGateway.objects.all()
    serializer_class = PaymentGatewaySerializer

class PaymentTransactionViewSet(BaseTenantViewSet):
    queryset = PaymentTransaction.objects.all()
    serializer_class = PaymentTransactionSerializer
    # ট্রানজেকশন সাধারণত API থেকে ডিলিট করা উচিত নয়
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

class PaymentSubscriptionViewSet(BaseTenantViewSet):
    queryset = PaymentSubscription.objects.all()
    serializer_class = PaymentSubscriptionSerializer

class PaymentRefundViewSet(BaseTenantViewSet):
    queryset = PaymentRefund.objects.all()
    serializer_class = PaymentRefundSerializer

class PaymentLogViewSet(viewsets.ReadOnlyModelViewSet):
    # লগগুলো সাধারণত শুধু পড়ার জন্য হয় (Read Only)
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentLogSerializer
    queryset = PaymentLog.objects.all()

    def get_queryset(self):
        return self.queryset.filter(tenant=self.request.user.tenant)