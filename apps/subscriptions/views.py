from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from .models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    👉 লাভজনক লজিক: প্ল্যান এপিআই সবার জন্য ওপেন (AllowAny)।
    যেকোনো ভিজিটর বা মার্চেন্ট অ্যাকাউন্ট খোলার আগেই প্ল্যান ও প্রাইসিং দেখতে পারবে।
    """
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]  # ➔ কোনো টোকেন লাগবে না, ব্রাউজারেও দেখা যাবে


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    👉 সুরক্ষিত লজিক: সাবস্ক্রিপশন কেনা, ক্যানসেল বা আপগ্রেড করা অত্যন্ত সংবেদনশীল।
    তাই এখানে লগইন বাধ্যতামূলক (IsAuthenticated)।
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]  # ➔ অবশ্যই ভ্যালিড টোকেন লাগবে

    def get_queryset(self):
        # সুপার এডমিন সব দেখতে পাবে, মার্চেন্ট শুধু তার নিজের স্টোরের সাবস্ক্রিপশন দেখবে
        user = self.request.user
        if user.role == 'super_admin':
            return Subscription.objects.all()
        return Subscription.objects.filter(tenant=user.tenant)

    @action(detail=True, methods=['POST'], url_path='cancel')
    def cancel_subscription(self, request, pk=None):
        """সাবস্ক্রিপশন ক্যানসেল করার কাস্টম এন্ডপয়েন্ট লজিক"""
        subscription = self.get_object()
        if subscription.status == 'canceled':
            return Response({"error": "Subscription is already canceled."}, status=status.HTTP_400_BAD_REQUEST)
        
        subscription.status = 'canceled'
        subscription.canceled_at = timezone.now()
        subscription.save()
        return Response({"message": "Subscription has been canceled successfully."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'], url_path='upgrade-downgrade')
    def upgrade_downgrade(self, request, pk=None):
        """প্ল্যান চেঞ্জ (Upgrade/Downgrade) করার কাস্টম এন্ডপয়েন্ট লজিক"""
        subscription = self.get_object()
        new_plan_id = request.data.get('plan_id')
        billing_cycle = request.data.get('billing_cycle', 'monthly')

        if not new_plan_id:
            return Response({"error": "plan_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_plan = Plan.objects.get(id=new_plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response({"error": "Selected plan is invalid or inactive."}, status=status.HTTP_404_NOT_FOUND)

        if subscription.plan == new_plan:
            return Response({"error": "Tenant is already on this plan."}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        subscription.plan = new_plan
        subscription.status = 'active'
        subscription.current_period_start = now
        
        if billing_cycle == 'yearly':
            subscription.current_period_end = now + timedelta(days=365)
        else:
            subscription.current_period_end = now + timedelta(days=30)

        subscription.save()
        return Response({
            "message": f"Successfully switched to {new_plan.display_name}.",
            "current_period_end": subscription.current_period_end
        }, status=status.HTTP_200_OK)