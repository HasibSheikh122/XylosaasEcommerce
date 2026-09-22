import logging
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from rest_framework import status, generics, views, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle

from apps.tenants.models import Tenant, Domain
from apps.tenants.serializers import (
    TenantRegistrationSerializer,
    MerchantStoreDetailSerializer,
)
from apps.subscriptions.models import Plan, Subscription

logger = logging.getLogger(__name__)
User = get_user_model()


class TenantRegistrationView(generics.CreateAPIView):
    """নতুন মার্চেন্ট স্টোর ও স্কিমা অনবোর্ডিং ভিউ[cite: 19]"""
    serializer_class = TenantRegistrationSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'tenant_creation'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                tenant = serializer.save()
                primary_domain = tenant.domains.filter(is_primary=True).first()
                domain_url = primary_domain.domain if primary_domain else f"{tenant.subdomain}.localhost"

            return Response({
                "status": "success",
                "message": "Your online store infrastructure has been provisioned successfully!",
                "data": {
                    "store_id": tenant.id,
                    "store_name": tenant.store_name,
                    "subdomain": tenant.subdomain,
                    "assigned_domain": domain_url,
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MerchantStoreDetailsView(generics.RetrieveUpdateAPIView):
    """মার্চেন্ট স্টোর ডিটেইলস ও সেটিংস ভিউ[cite: 19]"""
    serializer_class = MerchantStoreDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return getattr(self.request.user, 'tenant', None)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response({"status": "error", "message": "No active store found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response({"status": "error", "message": "No active store found."}, status=status.HTTP_404_NOT_FOUND)
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)


class StoreRegistrationView(views.APIView):
    """পাবলিক স্টোর অনবোর্ডিং ও পেমেন্ট ভেরিফিকেশন API[cite: 19]"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        store_name = data.get('store_name', '').strip()
        subdomain = data.get('subdomain', '').strip().lower()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        password = data.get('password', '')
        plan_id = data.get('plan')
        payment_method = data.get('payment_method', 'bkash')
        payment_trx_id = data.get('payment_trx_id', '').strip()

        if not store_name or not subdomain or not email or not password:
            return Response({'error': 'সকল প্রয়োজনীয় তথ্য পূরণ করুন।'}, status=status.HTTP_400_BAD_REQUEST)

        if Tenant.objects.filter(subdomain=subdomain).exists():
            return Response({'error': f"'{subdomain}' সাবডোমেনটি ইতোমধ্যে নিবন্ধিত রয়েছে।"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email__iexact=email).exists():
            return Response({'error': 'এই ইমেইল দিয়ে ইতোমধ্যে একটি অ্যাকাউন্ট খোলা হয়েছে।'}, status=status.HTTP_400_BAD_REQUEST)

        selected_plan = None
        if plan_id:
            selected_plan = Plan.objects.filter(id=plan_id, is_active=True).first()

        try:
            with transaction.atomic():
                now = timezone.now()

                # ১. টেন্যান্ট তৈরি (অ্যাপ্রুভালের পূর্বে নিষ্ক্রিয় থাকবে)[cite: 19]
                tenant = Tenant.objects.create(
                    schema_name=subdomain,
                    name=store_name,
                    store_name=store_name,
                    subdomain=subdomain,
                    plan=selected_plan,
                    is_active=False,
                    is_trial=False,
                    subscription_end_date=now + timedelta(days=30),
                    max_products=getattr(selected_plan, 'max_products', 100) if selected_plan else 100,
                    max_staff=getattr(selected_plan, 'max_staff', 5) if selected_plan else 5,
                    max_orders_per_month=getattr(selected_plan, 'max_orders_per_month', 500) if selected_plan else 500,
                )

                # ২. সাবডোমেন ডোমেন রেকর্ড তৈরি[cite: 19]
                Domain.objects.create(
                    domain=f"{subdomain}.localhost",
                    tenant=tenant,
                    is_primary=True
                )

                # ৩. কাস্টমার সিগন্যাল সাময়িকভাবে নিষ্ক্রিয় করে মার্চেন্ট অ্যাকাউন্ট তৈরি
                saved_receivers = post_save.receivers
                try:
                    post_save.receivers = []  # সিগন্যাল ডিসকানেক্ট রাখা হলো
                    User.objects.create_user(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        phone=phone,
                        role='merchant',
                        tenant=tenant,
                        is_staff=True,
                        is_active=True,
                    )
                finally:
                    post_save.receivers = saved_receivers  # সিগন্যাল পুনস্থাপন

                # ৪. সাবস্ক্রিপশন রেকর্ড সংরক্ষণ[cite: 19]
                if selected_plan:
                    Subscription.objects.create(
                        tenant=tenant,
                        plan=selected_plan,
                        status='active',
                        trial_start=now,
                        trial_end=now + timedelta(days=14),
                        current_period_start=now,
                        current_period_end=now + timedelta(days=30),
                        payment_provider=payment_method,
                        payment_provider_id=payment_trx_id
                    )

            return Response({
                'status': 'success',
                'message': 'দোকান তৈরির আবেদন সফল হয়েছে! সুপার অ্যাডমিনের অনুমোদনের পর ডোমেন চালু হবে।',
                'subdomain': subdomain
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': f"সার্ভার ত্রুটি: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)