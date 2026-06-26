from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import (
    SalesAnalytics, ProductAnalytics, CustomerAnalytics,
    CategoryAnalytics, RevenueAnalytics, TrafficAnalytics,
    RealtimeAnalytics, AnalyticsInsight, PerformanceMetrics, ExportReport
)

# Base Admin Configuration
class AnalyticsBaseAdmin(ModelAdmin):
    list_per_page = 25
    search_fields = ('tenant__store_name',)
    list_filter = ('tenant',)

@admin.register(SalesAnalytics)
class SalesAnalyticsAdmin(AnalyticsBaseAdmin):
    list_display = ('tenant', 'date', 'total_revenue', 'total_orders', 'net_revenue')
    list_filter = ('tenant', 'date')

@admin.register(ProductAnalytics)
class ProductAnalyticsAdmin(AnalyticsBaseAdmin):
    list_display = ('product', 'date', 'units_sold', 'revenue', 'conversion_rate')
    list_filter = ('tenant', 'date', 'product')

@admin.register(CustomerAnalytics)
class CustomerAnalyticsAdmin(AnalyticsBaseAdmin):
    list_display = ('customer', 'date', 'total_spent', 'segment', 'churn_risk_score')
    list_filter = ('tenant', 'segment')

@admin.register(CategoryAnalytics)
class CategoryAnalyticsAdmin(AnalyticsBaseAdmin):
    list_display = ('category', 'date', 'total_revenue', 'conversion_rate')
    list_filter = ('tenant', 'category')

@admin.register(RevenueAnalytics)
class RevenueAnalyticsAdmin(AnalyticsBaseAdmin):
    list_display = ('tenant', 'date', 'gross_profit', 'net_profit', 'profit_margin')
    list_filter = ('tenant', 'date')

@admin.register(TrafficAnalytics)
class TrafficAnalyticsAdmin(AnalyticsBaseAdmin):
    list_display = ('tenant', 'date', 'total_visitors', 'bounce_rate', 'conversion_rate')
    list_filter = ('tenant', 'date')

@admin.register(RealtimeAnalytics)
class RealtimeAnalyticsAdmin(AnalyticsBaseAdmin):
    list_display = ('tenant', 'timestamp', 'active_users', 'current_orders')
    readonly_fields = ('timestamp',)

@admin.register(AnalyticsInsight)
class AnalyticsInsightAdmin(AnalyticsBaseAdmin):
    list_display = ('title', 'tenant', 'insight_type', 'priority', 'is_read', 'is_resolved')
    list_filter = ('tenant', 'insight_type', 'priority', 'is_resolved')
    actions = ['mark_resolved']

    @admin.action(description="Mark selected insights as resolved")
    def mark_resolved(self, request, queryset):
        queryset.update(is_resolved=True)

@admin.register(PerformanceMetrics)
class PerformanceMetricsAdmin(AnalyticsBaseAdmin):
    list_display = ('tenant', 'month', 'monthly_revenue', 'customer_retention_rate')
    list_filter = ('tenant', 'month')

@admin.register(ExportReport)
class ExportReportAdmin(AnalyticsBaseAdmin):
    list_display = ('report_type', 'tenant', 'status', 'created_at', 'progress')
    list_filter = ('status', 'report_type', 'tenant')
    readonly_fields = ('created_at', 'file_url', 'progress')