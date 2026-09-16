import uuid
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.orders.models import Order
from .models import (
    PaymentGateway,
    PaymentTransaction,
    PaymentSubscription,
    PaymentRefund,
    PaymentLog,
)
from .serializers import (
    PaymentGatewaySerializer,
    PaymentTransactionSerializer,
    InitiatePaymentSerializer,
    PaymentRefundSerializer,
    PaymentSubscriptionSerializer,
    PaymentLogSerializer,
)


class BaseTenantPaymentViewSet(viewsets.ModelViewSet):
    """টেন্যান্ট ডেটা ফিল্টারিং ও নিরাপত্তা নিশ্চিতকারী বেস ভিউসেট"""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, 'tenant') and self.request.tenant:
            qs = qs.filter(tenant=self.request.tenant)
        return qs

    def perform_create(self, serializer):
        kwargs = {}
        if hasattr(self.request, 'tenant') and self.request.tenant:
            kwargs['tenant'] = self.request.tenant
        serializer.save(**kwargs)


class PaymentGatewayViewSet(BaseTenantPaymentViewSet):
    """স্টোরের পেমেন্ট গেটওয়ে কনফিগারেশন (মার্চেন্ট বা অ্যাডমিনের জন্য)"""
    queryset = PaymentGateway.objects.all()
    serializer_class = PaymentGatewaySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['gateway_type', 'is_active', 'is_default']

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        # নতুন গেটওয়ে ডিফল্ট হলে বাকিগুলোর ডিফল্ট স্ট্যাটাস তুলে নেওয়া
        if serializer.validated_data.get('is_default', False) and tenant:
            PaymentGateway.objects.filter(tenant=tenant).update(is_default=False)
        super().perform_create(serializer)


class PaymentTransactionViewSet(BaseTenantPaymentViewSet):
    """পেমেন্ট লেনদেন পরিচালনা, ইনিশিয়েশন ও গেটওয়ে হ্যান্ডলিং"""
    queryset = PaymentTransaction.objects.select_related('order', 'customer', 'gateway').all()
    serializer_class = PaymentTransactionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'currency']
    search_fields = ['transaction_id', 'order_number', 'gateway_transaction_id', 'customer_email']
    ordering_fields = ['amount', 'initiated_at']
    ordering = ['-initiated_at']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # সাধারণ কাস্টমার কেবল নিজের লেনদেন দেখতে পারবে
        if not user.is_staff and hasattr(user, 'customer_profile'):
            qs = qs.filter(customer=user.customer_profile)
        return qs

    @action(detail=False, methods=['post'], url_path='initiate')
    def initiate(self, request):
        """
        চেকআউট সম্পন্ন হওয়া কোনো অর্ডারের বিপরীতে অনলাইন পেমেন্ট সেশন শুরু করা
        """
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data['order_id']
        gateway_type = serializer.validated_data['gateway_type']
        payment_method = serializer.validated_data['payment_method']
        tenant = getattr(request, 'tenant', None)

        try:
            order = Order.objects.get(id=order_id, tenant=tenant)
        except Order.DoesNotExist:
            return Response({'error': 'অর্ডারটি খুঁজে পাওয়া যায়নি।'}, status=status.HTTP_404_NOT_FOUND)

        if order.payment_status == 'paid':
            return Response({'error': 'এই অর্ডারের মূল্য আগেই পরিশোধ করা হয়েছে।'}, status=status.HTTP_400_BAD_REQUEST)

        gateway = PaymentGateway.objects.filter(tenant=tenant, gateway_type=gateway_type, is_active=True).first()
        if not gateway:
            return Response({'error': f'{gateway_type} গেটওয়ে বর্তমানে নিষ্ক্রিয় বা অনুপলব্ধ।'}, status=status.HTTP_400_BAD_REQUEST)

        # ট্রানজাকশন আইডি ও ফি হিসাব
        tx_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        fee_amount = (order.total * (gateway.transaction_fee_percentage / Decimal('100.00'))) + gateway.transaction_fee_fixed
        net_amount = max(Decimal('0.00'), order.total - fee_amount)

        customer = getattr(request.user, 'customer_profile', None) if request.user.is_authenticated else order.customer

        payment_tx = PaymentTransaction.objects.create(
            tenant=tenant,
            order=order,
            customer=customer,
            gateway=gateway,
            transaction_id=tx_id,
            order_number=order.order_number,
            amount=order.total,
            currency='BDT',
            tax_amount=order.tax,
            fee_amount=fee_amount,
            discount_amount=order.discount,
            net_amount=net_amount,
            payment_method=payment_method,
            status='pending',
            customer_name=order.shipping_address.get('name', ''),
            customer_email=request.user.email if request.user.is_authenticated else '',
            customer_phone=order.shipping_address.get('phone', ''),
            billing_address=order.billing_address,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        PaymentLog.objects.create(
            tenant=tenant,
            transaction=payment_tx,
            log_type='request',
            log_data={'action': 'initiate_payment', 'gateway': gateway_type, 'amount': float(order.total)},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        # গেটওয়ে রিডাইরেক্ট লিঙ্ক সিমুলেশন
        redirect_url = f"https://payment-gateway.xylosaas.com/pay/{gateway_type}/{tx_id}"

        return Response({
            'transaction_id': tx_id,
            'amount': float(order.total),
            'currency': 'BDT',
            'gateway': gateway_type,
            'redirect_url': redirect_url,
            'status': payment_tx.status
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='webhook', permission_classes=[permissions.AllowAny])
    def webhook(self, request):
        """
        পেমেন্ট গেটওয়ে (SSLCommerz, bKash, Stripe ইত্যাদি) থেকে আসা আইপিএন/ওয়েবহুক লিসেনার
        """
        payload = request.data
        tx_id = payload.get('transaction_id') or payload.get('tran_id')
        gateway_status = payload.get('status', '').upper()
        gateway_tx_id = payload.get('val_id') or payload.get('payment_id') or payload.get('id', '')

        if not tx_id:
            return Response({'error': 'Transaction identifier missing'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tx = PaymentTransaction.objects.select_for_update().get(transaction_id=tx_id)
        except PaymentTransaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            PaymentLog.objects.create(
                tenant=tx.tenant,
                transaction=tx,
                log_type='webhook',
                log_data=payload,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            if gateway_status in ['COMPLETED', 'VALID', 'SUCCESS', 'PAID']:
                tx.status = 'completed'
                tx.gateway_transaction_id = gateway_tx_id
                tx.gateway_response = payload
                tx.completed_at = timezone.now()
                tx.save()

                if tx.order:
                    tx.order.payment_status = 'paid'
                    tx.order.status = 'processing'
                    tx.order.payment_id = gateway_tx_id
                    tx.order.save(update_fields=['payment_status', 'status', 'payment_id'])

                return Response({'status': 'Payment successfully verified and order updated'}, status=status.HTTP_200_OK)
            else:
                tx.status = 'failed'
                tx.gateway_error = payload.get('error_message', 'Payment was declined or cancelled.')
                tx.failed_at = timezone.now()
                tx.save()

                if tx.order:
                    tx.order.payment_status = 'failed'
                    tx.order.save(update_fields=['payment_status'])

                return Response({'status': 'Payment marked as failed'}, status=status.HTTP_200_OK)


class PaymentRefundViewSet(BaseTenantPaymentViewSet):
    """রিফান্ড প্রসেসিং ও অনুমোদন ম্যানেজমেন্ট"""
    queryset = PaymentRefund.objects.select_related('transaction', 'approved_by').all()
    serializer_class = PaymentRefundSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'is_approved', 'refund_reason']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        refund_id = f"REF-{uuid.uuid4().hex[:8].upper()}"
        kwargs = {
            'refund_transaction_id': refund_id,
            'status': 'pending'
        }
        if hasattr(self.request, 'tenant') and self.request.tenant:
            kwargs['tenant'] = self.request.tenant
        serializer.save(**kwargs)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """অ্যাডমিন কর্তৃক রিফান্ড অনুমোদন এবং ট্রানজাকশন হিস্ট্রি সিঙ্ক"""
        refund = self.get_object()
        if refund.is_approved:
            return Response({'error': 'এই রিফান্ডটি আগেই অনুমোদিত হয়েছে।'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            refund.is_approved = True
            refund.approved_by = request.user
            refund.status = 'completed'
            refund.processed_at = timezone.now()
            refund.save()

            tx = refund.transaction
            tx.refund_status = 'refunded'
            tx.refund_amount += refund.refund_amount
            tx.refund_transaction_id = refund.refund_transaction_id
            tx.refunded_at = timezone.now()
            tx.status = 'refunded' if tx.refund_amount >= tx.amount else 'partial_refund'
            tx.save()

            if tx.order:
                tx.order.status = 'refunded'
                tx.order.save(update_fields=['status'])

        return Response({'message': 'রিফান্ড সফলভাবে সম্পন্ন হয়েছে।', 'refund_id': refund.refund_transaction_id}, status=status.HTTP_200_OK)


class PaymentSubscriptionViewSet(BaseTenantPaymentViewSet):
    """SaaS সাবস্ক্রিপশন ফি পেমেন্ট হিস্ট্রি (Read-Only)"""
    queryset = PaymentSubscription.objects.select_related('subscription', 'transaction').all()
    serializer_class = PaymentSubscriptionSerializer
    http_method_names = ['get', 'head', 'options']


class PaymentLogViewSet(BaseTenantPaymentViewSet):
    """পেমেন্ট সিস্টেম ডিবাগিং ও অডিট ট্রেইল (Read-Only)"""
    queryset = PaymentLog.objects.select_related('transaction').all()
    serializer_class = PaymentLogSerializer
    http_method_names = ['get', 'head', 'options']
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['log_type']
    ordering = ['-created_at']