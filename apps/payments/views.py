import uuid
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
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
    InitiateSubscriptionPaymentSerializer,
    ManualSubscriptionPaymentSerializer,
    PaymentRefundSerializer,
    PaymentSubscriptionSerializer,
    PaymentLogSerializer,
)
from .sslcommerz import SSLCommerzService


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
    """স্টোরের পেমেন্ট গেটওয়ে কনফিগারেশন"""
    queryset = PaymentGateway.objects.all()
    serializer_class = PaymentGatewaySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['gateway_type', 'is_active', 'is_default']

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        if serializer.validated_data.get('is_default', False) and tenant:
            PaymentGateway.objects.filter(tenant=tenant).update(is_default=False)
        super().perform_create(serializer)


class PaymentTransactionViewSet(BaseTenantPaymentViewSet):
    """পেমেন্ট লেনদেন পরিচালনা, SSLCommerz অনলাইন ও ম্যানুয়াল TrxID হ্যান্ডলিং"""
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
        if user.is_authenticated and not user.is_staff and hasattr(user, 'customer_profile'):
            qs = qs.filter(customer=user.customer_profile)
        return qs

    # -------------------------------------------------------------
    # ১. চেকআউট অর্ডারের পেমেন্ট সেশন শুরু (SSLCommerz)
    # -------------------------------------------------------------
    @action(detail=False, methods=['post'], url_path='initiate')
    def initiate(self, request):
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

        gateway = None
        try:
            gateway = PaymentGateway.objects.filter(tenant=tenant, gateway_type=gateway_type, is_active=True).first()
        except Exception:
            gateway = None

        if not gateway and gateway_type != 'sslcommerz':
            return Response({'error': f'{gateway_type} গেটওয়ে বর্তমানে নিষ্ক্রিয় বা অনুপলব্ধ।'}, status=status.HTTP_400_BAD_REQUEST)

        tx_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        fee_pct = gateway.transaction_fee_percentage if gateway else Decimal('0.00')
        fee_fixed = gateway.transaction_fee_fixed if gateway else Decimal('0.00')
        fee_amount = (order.total * (fee_pct / Decimal('100.00'))) + fee_fixed
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
            customer_name=order.shipping_address.get('name', 'Customer'),
            customer_email=request.user.email if request.user.is_authenticated else 'customer@example.com',
            customer_phone=order.shipping_address.get('phone', '01700000000'),
            billing_address=order.billing_address or {},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        try:
            PaymentLog.objects.create(
                tenant=tenant,
                transaction=payment_tx,
                log_type='request',
                log_data={'action': 'initiate_payment', 'gateway': gateway_type, 'amount': float(order.total)},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception:
            pass

        if gateway_type == 'sslcommerz':
            ssl_service = SSLCommerzService(gateway=gateway)
            base_url = request.build_absolute_uri('/')[:-1]

            session_data = {
                "amount": order.total,
                "currency": "BDT",
                "transaction_id": tx_id,
                "customer_name": payment_tx.customer_name,
                "customer_email": payment_tx.customer_email,
                "customer_phone": payment_tx.customer_phone,
                "customer_address": order.shipping_address.get('address', 'Dhaka'),
                "product_name": f"Order #{order.order_number}",
                "success_url": f"{base_url}/api/v1/payments/transactions/sslcommerz-success/",
                "fail_url": f"{base_url}/api/v1/payments/transactions/sslcommerz-fail/",
                "cancel_url": f"{base_url}/api/v1/payments/transactions/sslcommerz-cancel/",
                "ipn_url": f"{base_url}/api/v1/payments/transactions/webhook/",
            }

            res = ssl_service.initiate_session(session_data)
            if res.get("success"):
                return Response({
                    'transaction_id': tx_id,
                    'amount': float(order.total),
                    'currency': 'BDT',
                    'gateway': 'sslcommerz',
                    'redirect_url': res["gateway_url"],
                    'status': 'pending'
                }, status=status.HTTP_201_CREATED)
            else:
                payment_tx.status = 'failed'
                payment_tx.gateway_error = res.get("error", "SSLCommerz Error")
                payment_tx.save()
                return Response({'error': res.get("error")}, status=status.HTTP_400_BAD_REQUEST)

        redirect_url = f"https://payment-gateway.xylosaas.com/pay/{gateway_type}/{tx_id}"
        return Response({
            'transaction_id': tx_id,
            'amount': float(order.total),
            'currency': 'BDT',
            'gateway': gateway_type,
            'redirect_url': redirect_url,
            'status': payment_tx.status
        }, status=status.HTTP_201_CREATED)

    # -------------------------------------------------------------
    # ২. SaaS প্ল্যান অনলাইন পেমেন্ট সেশন শুরু (SSLCommerz)
    # -------------------------------------------------------------
    @action(detail=False, methods=['post'], url_path='initiate-subscription', permission_classes=[permissions.AllowAny])
    def initiate_subscription(self, request):
        serializer = InitiateSubscriptionPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_name = serializer.validated_data['plan_name']
        amount = serializer.validated_data['amount']
        billing_cycle = serializer.validated_data['billing_cycle']

        tx_id = f"SUB-{uuid.uuid4().hex[:10].upper()}"
        tenant = getattr(request, 'tenant', None)
        
        gateway = None
        try:
            gateway = PaymentGateway.objects.filter(gateway_type='sslcommerz', is_active=True).first()
        except Exception:
            gateway = None

        payment_tx = PaymentTransaction.objects.create(
            tenant=tenant,
            gateway=gateway,
            transaction_id=tx_id,
            amount=amount,
            currency='BDT',
            payment_method='digital_wallet',
            status='pending',
            customer_name=serializer.validated_data.get('customer_name', 'Merchant Owner'),
            customer_email=serializer.validated_data.get('customer_email', 'merchant@example.com'),
            customer_phone=serializer.validated_data.get('customer_phone', '01700000000'),
            metadata={'is_subscription': True, 'plan_name': plan_name, 'billing_cycle': billing_cycle},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        ssl_service = SSLCommerzService(gateway=gateway)
        base_url = request.build_absolute_uri('/')[:-1]

        session_data = {
            "amount": amount,
            "currency": "BDT",
            "transaction_id": tx_id,
            "customer_name": payment_tx.customer_name,
            "customer_email": payment_tx.customer_email,
            "customer_phone": payment_tx.customer_phone,
            "product_name": f"SaaS Plan: {plan_name}",
            "success_url": f"{base_url}/api/v1/payments/transactions/sslcommerz-success/",
            "fail_url": f"{base_url}/api/v1/payments/transactions/sslcommerz-fail/",
            "cancel_url": f"{base_url}/api/v1/payments/transactions/sslcommerz-cancel/",
            "ipn_url": f"{base_url}/api/v1/payments/transactions/webhook/",
        }

        res = ssl_service.initiate_session(session_data)
        if res.get("success"):
            return Response({
                "transaction_id": tx_id,
                "gateway_url": res["gateway_url"]
            }, status=status.HTTP_200_OK)

        return Response({"error": res.get("error", "SSLCommerz সেশন তৈরিতে সমস্যা হয়েছে।")}, status=status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------
    # ৩. পূর্বের ম্যানুয়াল TrxID সাবমিশন (Send Money)
    # -------------------------------------------------------------
    @action(detail=False, methods=['post'], url_path='manual-subscription', permission_classes=[permissions.AllowAny])
    def manual_subscription(self, request):
        serializer = ManualSubscriptionPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_name = serializer.validated_data['plan_name']
        amount = serializer.validated_data['amount']
        sender_phone = serializer.validated_data.get('sender_phone', '')
        trx_id = serializer.validated_data['transaction_id'].strip().upper()

        if PaymentTransaction.objects.filter(transaction_id=trx_id).exists():
            return Response({'error': 'এই TrxID দিয়ে আগেই পেমেন্ট সাবমিট করা হয়েছে।'}, status=status.HTTP_400_BAD_REQUEST)

        tenant = getattr(request, 'tenant', None)

        PaymentTransaction.objects.create(
            tenant=tenant,
            transaction_id=trx_id,
            amount=amount,
            currency='BDT',
            payment_method='mobile_banking',
            status='pending',
            customer_phone=sender_phone,
            metadata={
                'is_subscription': True,
                'plan_name': plan_name,
                'is_manual_send_money': True,
                'sender_phone': sender_phone
            },
            notes=f"Manual Send Money Subscription for {plan_name}. Sender: {sender_phone}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'status': 'success',
            'message': 'পেমেন্ট ভেরিফিকেশনের জন্য সফলভাবে জমা হয়েছে।',
            'transaction_id': trx_id
        }, status=status.HTTP_201_CREATED)

    # -------------------------------------------------------------
    # ৪. SSLCommerz Success Callback (সঠিক পেজে রিডাইরেক্ট ফিক্স)
    # -------------------------------------------------------------
    @method_decorator(csrf_exempt)
    @action(detail=False, methods=['post', 'get'], url_path='sslcommerz-success', permission_classes=[permissions.AllowAny])
    def sslcommerz_success(self, request):
        data = request.data if request.method == 'POST' else request.GET
        tran_id = data.get('tran_id')
        val_id = data.get('val_id')

        try:
            tx = PaymentTransaction.objects.get(transaction_id=tran_id)
        except PaymentTransaction.DoesNotExist:
            return redirect("https://shop.xylotechsolution.com/?payment=failed&reason=transaction_not_found")

        ssl_service = SSLCommerzService(gateway=tx.gateway)
        val_result = ssl_service.validate_payment(val_id)

        if val_result.get("valid") and val_result.get("amount") >= tx.amount:
            with transaction.atomic():
                tx.status = 'completed'
                tx.gateway_transaction_id = val_id
                tx.gateway_response = data
                tx.completed_at = timezone.now()
                tx.save()

                if tx.metadata.get('is_subscription'):
                    plan_name = tx.metadata.get('plan_name')
                    billing_cycle = tx.metadata.get('billing_cycle', 'monthly')

                    PaymentSubscription.objects.create(
                        tenant=tx.tenant,
                        transaction=tx,
                        plan_name=plan_name,
                        plan_price=tx.amount,
                        billing_cycle=billing_cycle,
                        amount_paid=tx.amount,
                        period_start=timezone.now(),
                        period_end=timezone.now() + timezone.timedelta(days=30),
                        status='active'
                    )
                    # 🌟 ফিক্স: মূল পেজ /?status=success-এ রিডাইরেক্ট করা হচ্ছে (যাতে সরাসরি ৩ নম্বর ধাপ ওপেন হয়)
                    return redirect(f"https://shop.xylotechsolution.com/?status=success&tran_id={tran_id}")

                if tx.order:
                    tx.order.payment_status = 'paid'
                    tx.order.status = 'processing'
                    tx.order.payment_id = val_id
                    tx.order.save(update_fields=['payment_status', 'status', 'payment_id'])

                return redirect(f"/checkout/success?order_number={tx.order_number}&tran_id={tran_id}")
        else:
            tx.status = 'failed'
            tx.gateway_error = val_result.get("error", "Validation failed")
            tx.save()
            return redirect(f"https://shop.xylotechsolution.com/?payment=failed&tran_id={tran_id}")

    # -------------------------------------------------------------
    # ৫. SSLCommerz Fail & Cancel Callbacks
    # -------------------------------------------------------------
    @method_decorator(csrf_exempt)
    @action(detail=False, methods=['post', 'get'], url_path='sslcommerz-fail', permission_classes=[permissions.AllowAny])
    def sslcommerz_fail(self, request):
        tran_id = request.data.get('tran_id') or request.GET.get('tran_id')
        if tran_id:
            PaymentTransaction.objects.filter(transaction_id=tran_id).update(status='failed', failed_at=timezone.now())
        return redirect(f"https://shop.xylotechsolution.com/?payment=failed&tran_id={tran_id}")

    @method_decorator(csrf_exempt)
    @action(detail=False, methods=['post', 'get'], url_path='sslcommerz-cancel', permission_classes=[permissions.AllowAny])
    def sslcommerz_cancel(self, request):
        tran_id = request.data.get('tran_id') or request.GET.get('tran_id')
        if tran_id:
            PaymentTransaction.objects.filter(transaction_id=tran_id).update(status='cancelled')
        return redirect(f"https://shop.xylotechsolution.com/?payment=cancelled")

    # -------------------------------------------------------------
    # ৬. IPN / Webhook Listener (select_for_update ফিক্স)
    # -------------------------------------------------------------
    @action(detail=False, methods=['post'], url_path='webhook', permission_classes=[permissions.AllowAny])
    def webhook(self, request):
        payload = request.data
        tx_id = payload.get('transaction_id') or payload.get('tran_id')
        gateway_status = payload.get('status', '').upper()
        gateway_tx_id = payload.get('val_id') or payload.get('payment_id') or payload.get('id', '')

        if not tx_id:
            return Response({'error': 'Transaction identifier missing'}, status=status.HTTP_400_BAD_REQUEST)

        # 🌟 ফিক্স: select_for_update-কে transaction.atomic()-এর ভেতরে আনা হয়েছে
        with transaction.atomic():
            try:
                tx = PaymentTransaction.objects.select_for_update().get(transaction_id=tx_id)
            except PaymentTransaction.DoesNotExist:
                return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

            try:
                PaymentLog.objects.create(
                    tenant=tx.tenant,
                    transaction=tx,
                    log_type='webhook',
                    log_data=payload,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception:
                pass

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