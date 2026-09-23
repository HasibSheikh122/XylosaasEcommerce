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
    def get_queryset(self):
        qs = super().get_queryset()
        tenant = getattr(self.request, 'tenant', None)
        if not tenant and hasattr(self.request.user, 'tenant'):
            tenant = self.request.user.tenant
        if tenant:
            qs = qs.filter(tenant=tenant)
        return qs

    def perform_create(self, serializer):
        kwargs = {}
        tenant = getattr(self.request, 'tenant', None)
        if not tenant and hasattr(self.request.user, 'tenant'):
            tenant = self.request.user.tenant
        if tenant:
            kwargs['tenant'] = tenant
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
        # 🌟 Customer jate login charao review submit korte pare tai create action AllowAny
        if self.action in ['list', 'retrieve', 'create', 'helpful', 'not_helpful', 'product_summary']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        product_id = self.request.query_params.get('product')
        if product_id:
            qs = qs.filter(product_id=product_id)

        # Staff ba admin na hole verified ebong pending duto review-i storefront-e dekhabe
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(verification_status__in=['verified', 'pending'])
        return qs

    def perform_create(self, serializer):
        kwargs = {}
        tenant = getattr(self.request, 'tenant', None)
        if not tenant and hasattr(self.request.user, 'tenant'):
            tenant = self.request.user.tenant
        if tenant:
            kwargs['tenant'] = tenant

        kwargs['ip_address'] = self.request.META.get('REMOTE_ADDR')
        kwargs['user_agent'] = self.request.META.get('HTTP_USER_AGENT', '')

        if self.request.user.is_authenticated and hasattr(self.request.user, 'customer_profile'):
            kwargs['customer'] = self.request.user.customer_profile
            kwargs['is_anonymous'] = False
        else:
            kwargs['customer'] = None
            kwargs['is_anonymous'] = True

        kwargs['verification_status'] = 'verified'
        serializer.save(**kwargs)

    @action(detail=True, methods=['post'], url_path='helpful')
    def helpful(self, request, pk=None):
        review = self.get_object()
        review.mark_as_helpful()
        return Response({'status': 'vote recorded', 'helpful_count': review.helpful_count}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='not-helpful')
    def not_helpful(self, request, pk=None):
        review = self.get_object()
        review.mark_as_not_helpful()
        return Response({'status': 'vote recorded', 'not_helpful_count': review.not_helpful_count}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='product-summary/(?P<product_id>[^/.]+)')
    def product_summary(self, request, product_id=None):
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
    # 🌟 Storefront customer ebong merchant uboy-i jate reply create o list korte pare
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = getattr(self.request, 'tenant', None)
        if not tenant and hasattr(self.request.user, 'tenant'):
            tenant = self.request.user.tenant
        if tenant:
            qs = qs.filter(review__tenant=tenant)
        
        # 특정 review-er reply filter kora
        review_id = self.request.query_params.get('review')
        if review_id:
            qs = qs.filter(review_id=review_id)
            
        return qs.order_by('created_at')

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        is_owner = False
        
        # Staff ba admin hole Store Owner reply hishebe mark hobe
        if user and (user.is_staff or getattr(user, 'is_merchant', False)):
            is_owner = True
            
        serializer.save(
            user=user,
            is_owner_reply=is_owner,
            is_approved=True
        )
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


