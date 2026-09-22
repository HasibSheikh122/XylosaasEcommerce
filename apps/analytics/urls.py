from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SalesAnalyticsViewSet,
    ProductAnalyticsViewSet,
    CustomerAnalyticsViewSet,
    CategoryAnalyticsViewSet,
    RevenueAnalyticsViewSet,
    TrafficAnalyticsViewSet,
    RealtimeAnalyticsViewSet,
    AnalyticsInsightViewSet,
    PerformanceMetricsViewSet,
    ExportReportViewSet,
    DashboardSummaryView,  # 🌟 Added view
)

router = DefaultRouter()
router.register(r'sales', SalesAnalyticsViewSet, basename='analytics-sales')  #[cite: 17]
router.register(r'products', ProductAnalyticsViewSet, basename='analytics-product')  #[cite: 17]
router.register(r'customers', CustomerAnalyticsViewSet, basename='analytics-customer')  #[cite: 17]
router.register(r'categories', CategoryAnalyticsViewSet, basename='analytics-category')  #[cite: 17]
router.register(r'revenue', RevenueAnalyticsViewSet, basename='analytics-revenue')  #[cite: 17]
router.register(r'traffic', TrafficAnalyticsViewSet, basename='analytics-traffic')  #[cite: 17]
router.register(r'realtime', RealtimeAnalyticsViewSet, basename='analytics-realtime')  #[cite: 17]
router.register(r'insights', AnalyticsInsightViewSet, basename='analytics-insight')  #[cite: 17]
router.register(r'performance', PerformanceMetricsViewSet, basename='analytics-performance')  #[cite: 17]
router.register(r'exports', ExportReportViewSet, basename='analytics-export')  #[cite: 17]

urlpatterns = [
    path('summary/', DashboardSummaryView.as_view(), name='analytics-dashboard-summary'),
    path('', include(router.urls)),  #[cite: 17]
]