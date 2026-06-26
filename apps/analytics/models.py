from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class SalesAnalytics(models.Model):
    """Daily sales analytics for tenants"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    date = models.DateField()
    
    # Sales metrics
    total_orders = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_shipping = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Order metrics
    average_order_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_items_sold = models.IntegerField(default=0)
    average_items_per_order = models.FloatField(default=0)
    
    # Customer metrics
    unique_customers = models.IntegerField(default=0)
    new_customers = models.IntegerField(default=0)
    returning_customers = models.IntegerField(default=0)
    
    # Payment metrics
    total_refunds = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    refund_count = models.IntegerField(default=0)
    
    # Status breakdown
    completed_orders = models.IntegerField(default=0)
    pending_orders = models.IntegerField(default=0)
    cancelled_orders = models.IntegerField(default=0)
    failed_orders = models.IntegerField(default=0)
    
    # Shipping metrics
    average_shipping_time = models.FloatField(default=0)  # in hours
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_sales'
        unique_together = ['tenant', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['tenant', 'date']),
        ]
    
    def __str__(self):
        return f"{self.tenant.store_name} - {self.date}"

class ProductAnalytics(models.Model):
    """Product performance analytics"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    date = models.DateField()
    
    # Sales metrics
    units_sold = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Customer metrics
    unique_buyers = models.IntegerField(default=0)
    
    # Engagement metrics
    page_views = models.IntegerField(default=0)
    add_to_cart_count = models.IntegerField(default=0)
    wishlist_count = models.IntegerField(default=0)
    
    # Conversion metrics
    conversion_rate = models.FloatField(default=0)  # add_to_cart / page_views
    
    # Review metrics
    review_count = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0)
    
    # Inventory metrics
    stock_level = models.IntegerField(default=0)
    days_of_stock = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_product'
        unique_together = ['tenant', 'product', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['tenant', 'product', 'date']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.date}"

class CustomerAnalytics(models.Model):
    """Customer behavior analytics"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE)
    date = models.DateField()
    
    # Purchase metrics
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Engagement metrics
    days_since_last_purchase = models.IntegerField(default=0)
    purchase_frequency = models.FloatField(default=0)  # orders per month
    lifetime_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Behavior metrics
    items_per_order = models.FloatField(default=0)
    category_preferences = models.JSONField(default=list, blank=True)
    brand_preferences = models.JSONField(default=list, blank=True)
    
    # Session metrics
    total_sessions = models.IntegerField(default=0)
    avg_session_duration = models.IntegerField(default=0)  # in seconds
    bounce_rate = models.FloatField(default=0)
    
    # Churn metrics
    churn_risk_score = models.FloatField(default=0)
    churn_probability = models.FloatField(default=0)
    retention_score = models.FloatField(default=0)
    
    # Segment
    segment = models.CharField(max_length=50, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_customer'
        unique_together = ['tenant', 'customer', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['tenant', 'customer', 'date']),
        ]
    
    def __str__(self):
        return f"{self.customer.email} - {self.date}"

class CategoryAnalytics(models.Model):
    """Category performance analytics"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    category = models.ForeignKey('products.Category', on_delete=models.CASCADE)
    date = models.DateField()
    
    # Sales metrics
    total_orders = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_items_sold = models.IntegerField(default=0)
    
    # Performance metrics
    average_order_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    conversion_rate = models.FloatField(default=0)
    category_share = models.FloatField(default=0)  # percentage of total sales
    
    # Engagement
    page_views = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    
    # Subcategories
    subcategory_performance = models.JSONField(default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_category'
        unique_together = ['tenant', 'category', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.category.name} - {self.date}"

class RevenueAnalytics(models.Model):
    """Revenue breakdown analytics"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    date = models.DateField()
    
    # Revenue streams
    product_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    shipping_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    subscription_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Costs
    cost_of_goods_sold = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    operating_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    marketing_costs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Profit metrics
    gross_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    profit_margin = models.FloatField(default=0)
    gross_margin = models.FloatField(default=0)
    
    # Growth metrics
    revenue_growth = models.FloatField(default=0)  # percentage
    profit_growth = models.FloatField(default=0)  # percentage
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_revenue'
        unique_together = ['tenant', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.tenant.store_name} - {self.date}"

class TrafficAnalytics(models.Model):
    """Website traffic analytics"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    date = models.DateField()
    
    # Traffic metrics
    total_visitors = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    total_page_views = models.IntegerField(default=0)
    
    # Session metrics
    total_sessions = models.IntegerField(default=0)
    avg_session_duration = models.FloatField(default=0)  # in minutes
    bounce_rate = models.FloatField(default=0)
    pages_per_session = models.FloatField(default=0)
    
    # Traffic sources
    direct_traffic = models.IntegerField(default=0)
    organic_search = models.IntegerField(default=0)
    social_media = models.IntegerField(default=0)
    referral = models.IntegerField(default=0)
    email = models.IntegerField(default=0)
    paid_ads = models.IntegerField(default=0)
    
    # Device breakdown
    desktop_users = models.IntegerField(default=0)
    mobile_users = models.IntegerField(default=0)
    tablet_users = models.IntegerField(default=0)
    
    # Geographic
    top_countries = models.JSONField(default=list, blank=True)
    top_cities = models.JSONField(default=list, blank=True)
    
    # Conversion
    conversion_rate = models.FloatField(default=0)
    goal_completions = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_traffic'
        unique_together = ['tenant', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.tenant.store_name} - {self.date}"

class RealtimeAnalytics(models.Model):
    """Realtime analytics data"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Active users
    active_users = models.IntegerField(default=0)
    active_sessions = models.IntegerField(default=0)
    
    # Current visitors
    current_visitors = models.IntegerField(default=0)
    new_visitors = models.IntegerField(default=0)
    returning_visitors = models.IntegerField(default=0)
    
    # Current activity
    current_orders = models.IntegerField(default=0)
    current_cart_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_cart_count = models.IntegerField(default=0)
    
    # Page views
    page_views_last_hour = models.IntegerField(default=0)
    page_views_last_5min = models.IntegerField(default=0)
    
    # Top pages
    top_pages = models.JSONField(default=list, blank=True)
    
    # Sales this hour
    sales_this_hour = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    orders_this_hour = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_realtime'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.tenant.store_name} - {self.timestamp}"

class AnalyticsInsight(models.Model):
    """AI-generated insights and recommendations"""
    
    INSIGHT_TYPES = [
        ('sales', 'Sales Insight'),
        ('customer', 'Customer Insight'),
        ('product', 'Product Insight'),
        ('marketing', 'Marketing Insight'),
        ('inventory', 'Inventory Insight'),
        ('pricing', 'Pricing Insight'),
        ('churn', 'Churn Insight'),
        ('opportunity', 'Opportunity'),
        ('warning', 'Warning'),
        ('trend', 'Trend'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('critical', 'Critical Priority'),
    ]
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    recommendation = models.TextField(blank=True)
    
    # Related data
    related_product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True)
    related_customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True, blank=True)
    related_category = models.ForeignKey('products.Category', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metrics
    metric_name = models.CharField(max_length=100, blank=True)
    metric_value = models.FloatField(null=True, blank=True)
    metric_change = models.FloatField(null=True, blank=True)  # percentage
    
    # Confidence
    confidence_score = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Status
    is_read = models.BooleanField(default=False)
    is_acknowledged = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Data source
    data_source = models.CharField(max_length=100, blank=True)
    analysis_date = models.DateField(auto_now_add=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_insight'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'priority']),
            models.Index(fields=['tenant', 'insight_type']),
            models.Index(fields=['tenant', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.get_insight_type_display()} - {self.title}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])
    
    def mark_as_resolved(self, user):
        self.is_resolved = True
        self.resolved_at = models.DateTimeField(auto_now=True)
        self.resolved_by = user
        self.save(update_fields=['is_resolved', 'resolved_at', 'resolved_by'])

class PerformanceMetrics(models.Model):
    """Store performance metrics and KPIs"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    
    # Monthly metrics
    month = models.DateField()
    
    # Revenue KPIs
    monthly_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    monthly_orders = models.IntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Customer KPIs
    new_customers = models.IntegerField(default=0)
    repeat_customers = models.IntegerField(default=0)
    customer_retention_rate = models.FloatField(default=0)
    customer_acquisition_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Product KPIs
    top_products = models.JSONField(default=list, blank=True)
    top_categories = models.JSONField(default=list, blank=True)
    total_products_sold = models.IntegerField(default=0)
    
    # Operational KPIs
    order_fulfillment_time = models.FloatField(default=0)  # in days
    return_rate = models.FloatField(default=0)
    refund_rate = models.FloatField(default=0)
    
    # Marketing KPIs
    conversion_rate = models.FloatField(default=0)
    click_through_rate = models.FloatField(default=0)
    marketing_roi = models.FloatField(default=0)
    
    # Growth KPIs
    month_over_month_growth = models.FloatField(default=0)
    year_over_year_growth = models.FloatField(default=0)
    market_share = models.FloatField(default=0)
    
    # Targets
    revenue_target = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    orders_target = models.IntegerField(default=0)
    customer_target = models.IntegerField(default=0)
    
    # Achievement
    revenue_achievement = models.FloatField(default=0)  # percentage
    orders_achievement = models.FloatField(default=0)  # percentage
    customer_achievement = models.FloatField(default=0)  # percentage
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_performance'
        unique_together = ['tenant', 'month']
        ordering = ['-month']
    
    def __str__(self):
        return f"{self.tenant.store_name} - {self.month}"

class ExportReport(models.Model):
    """Exported analytics reports"""
    
    REPORT_TYPES = [
        ('sales', 'Sales Report'),
        ('customer', 'Customer Report'),
        ('product', 'Product Report'),
        ('inventory', 'Inventory Report'),
        ('financial', 'Financial Report'),
        ('marketing', 'Marketing Report'),
        ('custom', 'Custom Report'),
    ]
    
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
        ('json', 'JSON'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    requested_by = models.ForeignKey('users.User', on_delete=models.CASCADE)
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    report_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='csv')
    
    # Date range
    date_from = models.DateField()
    date_to = models.DateField()
    
    # Filters
    filters = models.JSONField(default=dict, blank=True)
    columns = models.JSONField(default=list, blank=True)  # selected columns
    group_by = models.JSONField(default=list, blank=True)
    sort_by = models.JSONField(default=list, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # File
    file_url = models.URLField(blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(default=0)  # in bytes
    
    # Progress
    progress = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Error
    error_message = models.TextField(blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # auto-delete after X days
    
    class Meta:
        db_table = 'analytics_export'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'requested_by']),
        ]
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.requested_by.email}"