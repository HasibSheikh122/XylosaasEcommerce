import logging
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from django.db import transaction

from apps.tenants.models import Tenant
from apps.tenants.serializers import (
    TenantRegistrationSerializer,
    MerchantStoreDetailSerializer,
)

logger = logging.getLogger(__name__)


class TenantRegistrationView(generics.CreateAPIView):
    """
    নতুন মার্চেন্ট স্টোর ও ডেডিকেটেড স্কিমা অনবোর্ডিং ভিউ
    """
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

            logger.info(f"New tenant schema '{tenant.schema_name}' successfully provisioned by {request.user.email}")
            
            return Response({
                "status": "success",
                "message": "Your online store infrastructure has been provisioned successfully!",
                "data": {
                    "store_id": tenant.id,
                    "store_name": tenant.store_name,
                    "subdomain": tenant.subdomain,
                    "assigned_domain": domain_url,
                    "plan_limits": {
                        "max_products": tenant.max_products,
                        "max_staff": tenant.max_staff,
                        "max_orders_per_month": tenant.max_orders_per_month,
                        "ai_enabled": tenant.ai_enabled
                    },
                    "subscription": {
                        "is_trial": tenant.is_trial,
                        "trial_ends_at": tenant.trial_ends_at,
                        "expiry_date": tenant.subscription_end_date
                    }
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Critical error during tenant provisioning for '{request.data.get('subdomain')}': {str(e)}")
            return Response({
                "status": "error",
                "message": "Failed to provision isolated database schema. Please contact system admin."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MerchantStoreDetailsView(generics.RetrieveUpdateAPIView):
    """
    মার্চেন্ট নিজের স্টোরের লিমিট দেখতে পারবে এবং লোগো/স্টোর নেম আপডেট করতে পারবে (GET, PUT, PATCH)
    """
    serializer_class = MerchantStoreDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user
        tenant = getattr(user, 'tenant', None)
        if not tenant:
            return None
        return tenant

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response(
                {"status": "error", "message": "You do not own or belong to any active store schema."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(instance)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response(
                {"status": "error", "message": "You do not have permission to update this store."},
                status=status.HTTP_404_NOT_FOUND
            )
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "status": "success",
            "message": "Store settings updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)