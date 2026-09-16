from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import StoreSettings, StoreStaff, StoreCategory, StorePage, StoreNotification
from .serializers import (
    StoreSettingsSerializer,
    PublicStoreSettingsSerializer,
    StoreStaffSerializer,
    StoreCategorySerializer,
    StorePageSerializer,
    StoreNotificationSerializer,
)


class BaseTenantStoreViewSet(viewsets.ModelViewSet):
    """টেন্যান্ট ডেটা ফিল্টারিংয়ের বেস ভিউসেট"""
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


class StoreSettingsViewSet(viewsets.ViewSet):
    """
    স্টোর সেটিংস কন্ট্রোলার:
    - সাধারণ ক্রেতাদের জন্য পাবলিক সেটিংস ভিউ (AllowAny)
    - মার্চেন্ট/স্টাফের জন্য সেটিংস আপডেট সুবিধা (IsAuthenticated)
    """
    def get_permissions(self):
        if self.action in ['retrieve', 'public']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_object(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            return None
        settings_obj, _ = StoreSettings.objects.get_or_create(
            tenant=tenant,
            defaults={
                'store_name': tenant.store_name,
                'subdomain': tenant.subdomain,
                'contact_email': getattr(self.request.user, 'email', 'store@xylosaas.com')
            }
        )
        return settings_obj

    def retrieve(self, request):
        settings_obj = self.get_object()
        if not settings_obj:
            return Response({'error': 'Tenant domain not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # অ্যাডমিন হলে সব ফিল্ড দেখাবে, ক্রেতা হলে শুধু পাবলিক ফিল্ডগুলো দেখাবে
        if request.user.is_authenticated and request.user.is_staff:
            serializer = StoreSettingsSerializer(settings_obj)
        else:
            serializer = PublicStoreSettingsSerializer(settings_obj)
        return Response(serializer.data)

    def update(self, request):
        settings_obj = self.get_object()
        if not settings_obj:
            return Response({'error': 'Tenant not recognized'}, status=status.HTTP_404_NOT_FOUND)

        serializer = StoreSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class StoreStaffViewSet(BaseTenantStoreViewSet):
    """দোকানের স্টাফ মেম্বার ও তাদের রোল/শিফট ম্যানেজমেন্ট"""
    queryset = StoreStaff.objects.select_related('user').all()
    serializer_class = StoreStaffSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['role', 'status', 'department']
    search_fields = ['user__email', 'employee_id', 'phone']


class StoreCategoryViewSet(BaseTenantStoreViewSet):
    """স্টোরফ্রন্ট ন্যাভিগেশন ও ক্যাটাগরি মেনু"""
    queryset = StoreCategory.objects.select_related('parent').all()
    serializer_class = StoreCategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'show_in_nav', 'show_on_homepage']
    search_fields = ['name', 'description']
    ordering_fields = ['display_order', 'name']
    ordering = ['display_order']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        if not (self.request.user and self.request.user.is_authenticated and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs


class StorePageViewSet(BaseTenantStoreViewSet):
    """কাস্টম পেজ ও পলিসি (About Us, FAQ, Privacy Policy ইত্যাদি)"""
    queryset = StorePage.objects.all()
    serializer_class = StorePageSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['page_type', 'is_published', 'show_in_footer', 'show_in_header']
    search_fields = ['title', 'content']
    ordering_fields = ['display_order', 'title']
    ordering = ['display_order']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        if not (self.request.user and self.request.user.is_authenticated and self.request.user.is_staff):
            qs = qs.filter(is_published=True)
        return qs

    def perform_create(self, serializer):
        kwargs = {'created_by': self.request.user}
        if hasattr(self.request, 'tenant') and self.request.tenant:
            kwargs['tenant'] = self.request.tenant
        serializer.save(**kwargs)


class StoreNotificationViewSet(BaseTenantStoreViewSet):
    """ঘোষণা ও ব্যানার নোটিফিকেশন"""
    queryset = StoreNotification.objects.all()
    serializer_class = StoreNotificationSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['notification_type', 'priority', 'is_popup', 'is_active']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'active_announcements']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='active-announcements')
    def active_announcements(self, request):
        """স্টোরফ্রন্টে দেখানোর জন্য সক্রিয় নোটিফিকেশন ব্যানার"""
        now = timezone.now()
        qs = self.get_queryset().filter(
            is_active=True,
            publish_from__lte=now
        ).exclude(publish_to__lt=now)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)