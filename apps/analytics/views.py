from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import (
    SalesAnalytics,
    ProductAnalytics,
    CustomerAnalytics,
    CategoryAnalytics,
    RevenueAnalytics,
    TrafficAnalytics,
    RealtimeAnalytics,
    AnalyticsInsight,
    PerformanceMetrics,
    ExportReport,
)
from .serializers import (
    SalesAnalyticsSerializer,
    ProductAnalyticsSerializer,
    CustomerAnalyticsSerializer,
    CategoryAnalyticsSerializer,
    RevenueAnalyticsSerializer,
    TrafficAnalyticsSerializer,
    RealtimeAnalyticsSerializer,
    AnalyticsInsightSerializer,
    PerformanceMetricsSerializer,
    ExportReportSerializer,
)


class BaseAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """অ্যানালিটিক্স ডেটার জন্য রিড-অনলি বেস ভিউসেট (টেন্যান্ট আইসোলেশন সহ)"""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, 'tenant'):
            qs = qs.filter(tenant=self.request.tenant)
        return qs


class SalesAnalyticsViewSet(BaseAnalyticsViewSet):
    queryset = SalesAnalytics.objects.all()
    serializer_class = SalesAnalyticsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {'date': ['exact', 'gte', 'lte']}
    ordering_fields = ['date', 'total_revenue', 'total_orders']
    ordering = ['-date']


class ProductAnalyticsViewSet(BaseAnalyticsViewSet):
    queryset = ProductAnalytics.objects.select_related('product').all()
    serializer_class = ProductAnalyticsSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {'product': ['exact'], 'date': ['exact', 'gte', 'lte']}
    search_fields = ['product__name']
    ordering_fields = ['revenue', 'units_sold', 'page_views', 'conversion_rate']
    ordering = ['-date']


class CustomerAnalyticsViewSet(BaseAnalyticsViewSet):
    queryset = CustomerAnalytics.objects.select_related('customer').all()
    serializer_class = CustomerAnalyticsSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {'customer': ['exact'], 'segment': ['exact'], 'date': ['exact', 'gte', 'lte']}
    search_fields = ['customer__email']
    ordering_fields = ['lifetime_value', 'total_spent', 'churn_risk_score']
    ordering = ['-date']


class CategoryAnalyticsViewSet(BaseAnalyticsViewSet):
    queryset = CategoryAnalytics.objects.select_related('category').all()
    serializer_class = CategoryAnalyticsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {'category': ['exact'], 'date': ['exact', 'gte', 'lte']}
    ordering_fields = ['total_revenue', 'total_orders', 'conversion_rate']
    ordering = ['-date']


class RevenueAnalyticsViewSet(BaseAnalyticsViewSet):
    queryset = RevenueAnalytics.objects.all()
    serializer_class = RevenueAnalyticsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {'date': ['exact', 'gte', 'lte']}
    ordering_fields = ['date', 'net_profit', 'gross_profit', 'profit_margin']
    ordering = ['-date']


class TrafficAnalyticsViewSet(BaseAnalyticsViewSet):
    queryset = TrafficAnalytics.objects.all()
    serializer_class = TrafficAnalyticsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {'date': ['exact', 'gte', 'lte']}
    ordering_fields = ['date', 'total_visitors', 'total_page_views', 'bounce_rate']
    ordering = ['-date']


class RealtimeAnalyticsViewSet(BaseAnalyticsViewSet):
    queryset = RealtimeAnalytics.objects.all()
    serializer_class = RealtimeAnalyticsSerializer
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'], url_path='latest')
    def latest(self, request):
        """লাইভ ড্যাশবোর্ডের জন্য সর্বশেষ রিয়েল-টাইম মেট্রিক"""
        latest_record = self.get_queryset().first()
        if not latest_record:
            return Response({'message': 'No realtime data available'}, status=status.HTTP_204_NO_CONTENT)
        return Response(self.get_serializer(latest_record).data)


class AnalyticsInsightViewSet(viewsets.ModelViewSet):
    queryset = AnalyticsInsight.objects.select_related('related_product', 'related_customer', 'related_category').all()
    serializer_class = AnalyticsInsightSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['insight_type', 'priority', 'is_read', 'is_resolved']
    ordering_fields = ['priority', 'created_at', 'confidence_score']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, 'tenant'):
            qs = qs.filter(tenant=self.request.tenant)
        return qs

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        insight = self.get_object()
        insight.mark_as_read()
        return Response({'status': 'marked as read'})

    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve(self, request, pk=None):
        insight = self.get_object()
        insight.mark_as_resolved(user=request.user)
        return Response({'status': 'resolved', 'resolved_by': request.user.email})


class PerformanceMetricsViewSet(BaseAnalyticsViewSet):
    queryset = PerformanceMetrics.objects.all()
    serializer_class = PerformanceMetricsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {'month': ['exact', 'gte', 'lte']}
    ordering_fields = ['month', 'monthly_revenue', 'monthly_orders']
    ordering = ['-month']


class ExportReportViewSet(viewsets.ModelViewSet):
    queryset = ExportReport.objects.select_related('requested_by').all()
    serializer_class = ExportReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['report_type', 'status', 'report_format']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, 'tenant'):
            qs = qs.filter(tenant=self.request.tenant)
        return qs

    def perform_create(self, serializer):
        kwargs = {'requested_by': self.request.user}
        if hasattr(self.request, 'tenant'):
            kwargs['tenant'] = self.request.tenant
        serializer.save(**kwargs)