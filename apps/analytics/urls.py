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
)

router = DefaultRouter()
router.register(r'sales', SalesAnalyticsViewSet, basename='analytics-sales')
router.register(r'products', ProductAnalyticsViewSet, basename='analytics-product')
router.register(r'customers', CustomerAnalyticsViewSet, basename='analytics-customer')
router.register(r'categories', CategoryAnalyticsViewSet, basename='analytics-category')
router.register(r'revenue', RevenueAnalyticsViewSet, basename='analytics-revenue')
router.register(r'traffic', TrafficAnalyticsViewSet, basename='analytics-traffic')
router.register(r'realtime', RealtimeAnalyticsViewSet, basename='analytics-realtime')
router.register(r'insights', AnalyticsInsightViewSet, basename='analytics-insight')
router.register(r'performance', PerformanceMetricsViewSet, basename='analytics-performance')
router.register(r'exports', ExportReportViewSet, basename='analytics-export')

urlpatterns = [
    path('', include(router.urls)),
]