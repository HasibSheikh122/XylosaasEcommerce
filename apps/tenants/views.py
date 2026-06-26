from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from django.conf import settings
from django.db import transaction
import logging

from apps.tenants.models import Tenant, Domain
from apps.tenants.serializers import TenantRegistrationSerializer

# লগ ট্র্যাকিং করার জন্য (প্রোডাকশনে এরর ট্র্যাক করতে হেল্প করবে)
logger = logging.getLogger(__name__)

class TenantRegistrationView(generics.CreateAPIView):
    """
    SaaS Merchantদের জন্য আল্ট্রা-অ্যাডভান্সড স্টোর/টেন্যান্ট ক্রিয়েশন ভিউ।
    এখানে সিকিউরিটি, রেট-লিমিট এবং ডাইনামিক ডোমেন কনফিগারেশন হ্যান্ডেল করা হয়েছে।
    """
    serializer_class = TenantRegistrationSerializer
    permission_classes = [IsAuthenticated] # শুধুমাত্র লগইন করা ইউজাররাই শপ খুলতে পারবে
    
    # 🔒 স্প্যাম প্রোটেকশন: একজন ইউজার দিনে বা ঘণ্টায় কয়বার দোকান খোলার ট্রাই করতে পারবে তা লক করা
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'tenant_creation' # settings.py এ এর রেট সেট করতে পারবেন (যেমন: 3/day)

    def create(self, request, *args, **kwargs):
        # সিরিয়ালাইজারে রিকোয়েস্ট কনটেক্সট পাস করা (যাতে request.user অ্যাক্সেস করা যায়)
        serializer = self.get_serializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # ডাটাবেস ট্রানজেকশন সেফটি নিশ্চিত করে অবজেক্ট ক্রিয়েট করা
            with transaction.atomic():
                tenant = serializer.save()
                
                # ডাইনামিকালি প্রাইমারি ডোমেন অবজেক্টটি তুলে আনা (যা সিরিয়ালাইজারে তৈরি হয়েছে)
                primary_domain = tenant.domains.filter(is_primary=True).first()
                domain_url = primary_domain.domain if primary_domain else f"{tenant.subdomain}.localhost"

            # 🚀 সাকসেস রেসপন্স (এখানে ফ্রন্টএন্ডের জন্য প্রয়োজনীয় সব মেটাডেটা পাঠানো হচ্ছে)
            logger.info(f"New tenant/schema '{tenant.schema_name}' successfully created by user {request.user.email}")
            
            return Response({
                "status": "success",
                "message": "Your online store infrastructure has been provisioned successfully!",
                "data": {
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
            # কোনো কারণে সিস্টেমে এরর হলে তা লগে পুশ করা এবং সেফ রেসপন্স দেওয়া
            logger.error(f"Critical error during tenant provisioning for subdomain '{request.data.get('subdomain')}': {str(e)}")
            return Response({
                "status": "error",
                "message": "An internal error occurred while setting up your store isolated database. Please contact support."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MerchantStoreDetailsView(generics.RetrieveAPIView):
    """
    কারেন্ট লগইন থাকা ওনার (Owner) যেন তার নিজস্ব স্টোরের লিমিট এবং সেটিংস দেখতে পারে
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.tenant:
            return Response(
                {"status": "error", "message": "You do not own or belong to any store active schema."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        tenant = user.tenant
        return Response({
            "status": "success",
            "data": {
                "store_id": tenant.id,
                "store_name": tenant.store_name,
                "subdomain": tenant.subdomain,
                "schema_name": tenant.schema_name,
                "is_active": tenant.is_active,
                "limits": {
                    "max_products": tenant.max_products,
                    "max_staff": tenant.max_staff,
                    "max_orders_per_month": tenant.max_orders_per_month,
                    "ai_enabled": tenant.ai_enabled
                }
            }
        }, status=status.HTTP_200_OK)