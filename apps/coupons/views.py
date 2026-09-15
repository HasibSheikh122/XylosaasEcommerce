from decimal import Decimal
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.customers.models import Customer
from .models import Coupon, CouponUsage, CouponRule, CouponCategory
from .serializers import (
    CouponSerializer,
    CouponUsageSerializer,
    CouponRuleSerializer,
    CouponCategorySerializer,
    ValidateCouponRequestSerializer,
)


class BaseTenantViewSet(viewsets.ModelViewSet):
    """টেন্যান্ট আইসোলেশন ও ডেটা ফিল্টারিং হ্যান্ডলার"""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, 'tenant'):
            qs = qs.filter(tenant=self.request.tenant)
        return qs

    def perform_create(self, serializer):
        kwargs = {}
        if hasattr(self.request, 'tenant'):
            kwargs['tenant'] = self.request.tenant
        serializer.save(**kwargs)


class CouponCategoryViewSet(BaseTenantViewSet):
    queryset = CouponCategory.objects.all()
    serializer_class = CouponCategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name']


class CouponViewSet(BaseTenantViewSet):
    queryset = Coupon.objects.prefetch_related('rules', 'applicable_categories', 'applicable_products').all()
    serializer_class = CouponSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'discount_type', 'is_public', 'show_on_checkout']
    search_fields = ['code', 'name']
    ordering_fields = ['priority', 'valid_to', 'created_at']

    def perform_create(self, serializer):
        kwargs = {}
        if hasattr(self.request, 'tenant'):
            kwargs['tenant'] = self.request.tenant
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user
        serializer.save(**kwargs)

    @action(detail=False, methods=['post'], url_path='validate-coupon', permission_classes=[permissions.AllowAny])
    def validate_coupon(self, request):
        """
        চেকআউট কার্টে কুপন কোডের লাইভ ভ্যালিডিটি ও ডিসকাউন্ট নির্ণয় করার পাবলিক API
        """
        serializer = ValidateCouponRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code'].strip()
        cart_total = serializer.validated_data['cart_total']
        customer_id = serializer.validated_data.get('customer_id')

        # টেন্যান্ট ফিল্টারিং
        qs = Coupon.objects.filter(code__iexact=code)
        if hasattr(request, 'tenant'):
            qs = qs.filter(tenant=request.tenant)

        coupon = qs.first()
        if not coupon:
            return Response({'is_valid': False, 'message': 'কুপন কোডটি সঠিক নয়।'}, status=status.HTTP_404_NOT_FOUND)

        # কাস্টমার বের করা
        customer = None
        if customer_id:
            customer = Customer.objects.filter(id=customer_id).first()

        # মডেল মেথড দিয়ে ভ্যালিডেশন
        is_valid, message = coupon.is_valid(cart_total=cart_total, customer=customer)
        if not is_valid:
            return Response({'is_valid': False, 'message': message}, status=status.HTTP_400_BAD_REQUEST)

        # ডিসকাউন্ট গণনা
        discount_amount = coupon.calculate_discount(cart_total=cart_total)
        final_total = max(Decimal('0.00'), cart_total - discount_amount)

        return Response({
            'is_valid': True,
            'message': 'কুপন সফলভাবে প্রয়োগ করা হয়েছে।',
            'code': coupon.code,
            'discount_type': coupon.discount_type,
            'discount_amount': float(discount_amount),
            'final_amount': float(final_total),
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='checkout-available', permission_classes=[permissions.AllowAny])
    def checkout_available(self, request):
        """চেকআউট পেজে ইউজারদের দেখানোর মতো পাবলিক ও অ্যাক্টিভ কুপন তালিকা"""
        now = timezone.now()
        qs = self.get_queryset().filter(
            status='active',
            show_on_checkout=True,
            is_public=True,
            valid_from__lte=now,
            valid_to__gte=now
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class CouponRuleViewSet(viewsets.ModelViewSet):
    queryset = CouponRule.objects.select_related('coupon').all()
    serializer_class = CouponRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, 'tenant'):
            qs = qs.filter(coupon__tenant=self.request.tenant)
        return qs


class CouponUsageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CouponUsage.objects.select_related('coupon', 'order', 'customer').all()
    serializer_class = CouponUsageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['coupon', 'customer', 'order', 'is_valid']
    ordering_fields = ['used_at']
    ordering = ['-used_at']

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, 'tenant'):
            qs = qs.filter(coupon__tenant=self.request.tenant)
        return qs