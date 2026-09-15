from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Review, ReviewReply, ReviewReport, ReviewPhoto, ReviewAnalytics, ReviewTemplate
from .serializers import (
    ReviewSerializer,
    ReviewReplySerializer,
    ReviewReportSerializer,
    ReviewPhotoSerializer,
    ReviewAnalyticsSerializer,
    ReviewTemplateSerializer,
)


class BaseTenantViewSet(viewsets.ModelViewSet):
    """টেন্যান্ট অনুযায়ী কুয়েরিসেট আইসোলেট করার বেস ভিউসেট"""
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


class ReviewViewSet(BaseTenantViewSet):
    queryset = Review.objects.select_related('customer', 'product').prefetch_related('replies', 'review_photos').all()
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product', 'rating', 'verification_status', 'verified_purchase', 'is_featured']
    search_fields = ['title', 'content', 'product__name']
    ordering_fields = ['rating', 'helpful_count', 'created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        # সাধারণ ক্যাটালগে রিভিউ যে কেউ পড়তে পারবে, তবে সাবমিট করতে লগইন দরকার
        if self.action in ['list', 'retrieve', 'helpful', 'not_helpful', 'product_summary']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        # সাধারণ ভিজিটরদের শুধু ভেরিফায়েড রিভিউ দেখানো হবে
        if not self.request.user.is_staff:
            qs = qs.filter(verification_status='verified')
        return qs

    def perform_create(self, serializer):
        kwargs = {}
        if hasattr(self.request, 'tenant'):
            kwargs['tenant'] = self.request.tenant
        
        # আইপি অ্যাড্রেস ও ইউজার এজেন্ট সংরক্ষণ
        kwargs['ip_address'] = self.request.META.get('REMOTE_ADDR')
        kwargs['user_agent'] = self.request.META.get('HTTP_USER_AGENT', '')
        
        # ইউজার যদি কাস্টমার অ্যাকাউন্টের সাথে লিঙ্কড থাকে
        if hasattr(self.request.user, 'customer_profile'):
            kwargs['customer'] = self.request.user.customer_profile
            
        serializer.save(**kwargs)

    @action(detail=True, methods=['post'], url_path='helpful')
    def helpful(self, request, pk=None):
        """রিভিউতে হেল্পফুল আপভোট দেওয়া"""
        review = self.get_object()
        review.mark_as_helpful()
        return Response({'status': 'vote recorded', 'helpful_count': review.helpful_count}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='not-helpful')
    def not_helpful(self, request, pk=None):
        """রিভিউতে আনহেল্পফুল ডাউনভোট দেওয়া"""
        review = self.get_object()
        review.mark_as_not_helpful()
        return Response({'status': 'vote recorded', 'not_helpful_count': review.not_helpful_count}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='product-summary/(?P<product_id>[^/.]+)')
    def product_summary(self, request, product_id=None):
        """নির্দিষ্ট একটি প্রোডাক্টের এভারেজ রেটিং ও রেটিং ডিস্ট্রিবিউশন প্রদান"""
        reviews = self.get_queryset().filter(product_id=product_id)
        if not reviews.exists():
            return Response({'total_reviews': 0, 'average_rating': 0, 'distribution': {i: 0 for i in range(1, 6)}})

        first_rev = reviews.first()
        return Response({
            'total_reviews': reviews.count(),
            'average_rating': first_rev.get_average_rating() or 0,
            'distribution': first_rev.get_rating_distribution(),
        })


class ReviewReplyViewSet(viewsets.ModelViewSet):
    queryset = ReviewReply.objects.select_related('review', 'user').all()
    serializer_class = ReviewReplySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, 'tenant'):
            qs = qs.filter(review__tenant=self.request.tenant)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, is_owner_reply=self.request.user.is_staff)


class ReviewReportViewSet(viewsets.ModelViewSet):
    queryset = ReviewReport.objects.select_related('review', 'reported_by').all()
    serializer_class = ReviewReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, 'tenant'):
            qs = qs.filter(review__tenant=self.request.tenant)
        return qs


class ReviewPhotoViewSet(viewsets.ModelViewSet):
    queryset = ReviewPhoto.objects.select_related('review').all()
    serializer_class = ReviewPhotoSerializer
    permission_classes = [permissions.IsAuthenticated]


class ReviewAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReviewAnalytics.objects.select_related('product', 'tenant').all()
    serializer_class = ReviewAnalyticsSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, 'tenant'):
            qs = qs.filter(tenant=self.request.tenant)
        return qs


class ReviewTemplateViewSet(BaseTenantViewSet):
    queryset = ReviewTemplate.objects.all()
    serializer_class = ReviewTemplateSerializer
    permission_classes = [permissions.IsAdminUser]