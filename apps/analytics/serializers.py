from rest_framework import serializers
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


class SalesAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesAnalytics
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class ProductAnalyticsSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ProductAnalytics
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class CustomerAnalyticsSerializer(serializers.ModelSerializer):
    customer_email = serializers.CharField(source='customer.email', read_only=True)

    class Meta:
        model = CustomerAnalytics
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class CategoryAnalyticsSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = CategoryAnalytics
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class RevenueAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RevenueAnalytics
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class TrafficAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficAnalytics
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class RealtimeAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RealtimeAnalytics
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'timestamp', 'created_at']


class AnalyticsInsightSerializer(serializers.ModelSerializer):
    insight_type_display = serializers.CharField(source='get_insight_type_display', read_only=True)

    class Meta:
        model = AnalyticsInsight
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'analysis_date', 'resolved_at', 'resolved_by', 'created_at', 'updated_at']


class PerformanceMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceMetrics
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class ExportReportSerializer(serializers.ModelSerializer):
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    requested_by_email = serializers.CharField(source='requested_by.email', read_only=True)

    class Meta:
        model = ExportReport
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'requested_by', 'status', 'file_url', 'file_path', 'file_size', 'progress', 'created_at', 'completed_at']