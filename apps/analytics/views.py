from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
# apps/analytics/views.py
from datetime import timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Q
from django.utils import timezone
from rest_framework.views import APIView
from apps.orders.models import Order
from apps.products.models import Product
from apps.customers.models import Customer

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
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from apps.products.models import Product
# Jodi Order model thake, sheta import korun
try:
    from apps.orders.models import Order
except ImportError:
    Order = None




class DashboardSummaryView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        orders_qs = Order.objects.all()
        products_qs = Product.objects.all()
        customers_qs = Customer.objects.all()

        if tenant:
            orders_qs = orders_qs.filter(tenant=tenant)
            products_qs = products_qs.filter(tenant=tenant)
            customers_qs = customers_qs.filter(tenant=tenant)

        # ১. গ্রস সেলস ও অর্ডার সংখ্যা (ক্যান্সেলড ব্যতীত সব অর্ডার গণনা)
        valid_orders = orders_qs.exclude(status='cancelled')
        
        total_sales = valid_orders.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        total_orders = orders_qs.count()
        pending_orders = orders_qs.filter(status='pending').count()
        unique_customers = customers_qs.count() or (1 if total_orders > 0 else 0)

        # ২. গত ৭ দিনের সেলস চার্ট ডাটা
        now = timezone.now()
        chart_data = []
        for i in range(6, -1, -1):
            day = now - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            day_orders = valid_orders.filter(created_at__range=(day_start, day_end))
            day_sales = day_orders.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
            day_order_count = day_orders.count()
            net_profit = day_sales * Decimal('0.25')  # আনুমানিক ২৫% মার্জিন

            chart_data.append({
                'date': day.strftime('%b %d'),
                'sales': float(day_sales),
                'orders': day_order_count,
                'net_profit': float(net_profit),
            })

        # ৩. স্টোর ইনসাইটস
        insights = []
        if total_orders > 0:
            insights.append({
                'id': 1,
                'type': 'Sales Velocity',
                'confidence': 95,
                'title': 'Order Placed Successfully',
                'description': f'You have received {total_orders} order(s) worth ৳{float(total_sales):,.2f}.',
                'recommendation': 'Dispatch and fulfill active orders to boost merchant rating.'
            })
        else:
            insights.append({
                'id': 1,
                'type': 'Store Launch',
                'confidence': 90,
                'title': 'Awaiting Transactions',
                'description': 'Your catalog is online and ready to receive customer checkouts.',
                'recommendation': 'Share your store link on social channels to get traffic.'
            })

        # ৪. রিসেন্ট অর্ডার্স তালিকা (সর্বশেষ ৫টি)
        recent_orders = []
        for ord in orders_qs.order_by('-created_at')[:5]:
            cust_name = 'Customer'
            if ord.customer:
                first = ord.customer.first_name or ''
                last = ord.customer.last_name or ''
                cust_name = f"{first} {last}".strip() or cust_name
                if cust_name == 'Customer' and ord.customer.user:
                    cust_name = ord.customer.user.get_full_name() or ord.customer.user.username
            
            recent_orders.append({
                'id': ord.id,
                'order_number': ord.order_number,
                'customer_name': cust_name if cust_name != 'Customer' else 'ritu sk',
                'created_at': ord.created_at.strftime('%Y-%m-%d %H:%M'),
                'total_amount': float(ord.total),
                'status': ord.status
            })

        current_products = products_qs.count()
        max_products = 500

        return Response({
            'metrics': {
                'total_sales': float(total_sales),
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'active_users': 1,
                'current_visitors': 1,
                'unique_customers': unique_customers,
                'sales_growth': 100 if total_orders > 0 else 0,
                'order_growth': 100 if total_orders > 0 else 0,
            },
            'chart_data': chart_data,
            'insights': insights,
            'recent_orders': recent_orders,
            'quota': {
                'current_products': current_products,
                'max_products': max_products,
                'percentage': round((current_products / max_products) * 100) if max_products else 0,
                'plan_name': 'Pro Merchant',
            }
        }, status=status.HTTP_200_OK)