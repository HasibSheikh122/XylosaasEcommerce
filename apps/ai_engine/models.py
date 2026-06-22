# apps/ai_engine/models.py
from django.db import models

class AIRecommendation(models.Model):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    
    score = models.FloatField()
    reason = models.CharField(max_length=255, blank=True)
    viewed = models.BooleanField(default=False)
    clicked = models.BooleanField(default=False)
    purchased = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_recommendations'
        indexes = [
            models.Index(fields=['tenant', 'customer', 'created_at']),
        ]

class ChatbotInteraction(models.Model):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, null=True)
    session_id = models.CharField(max_length=255)
    
    question = models.TextField()
    response = models.TextField()
    intent = models.CharField(max_length=100, blank=True)
    confidence = models.FloatField(default=0)
    was_helpful = models.BooleanField(null=True)
    
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_chatbot_interactions'

class DemandForecast(models.Model):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    
    forecast_date = models.DateField()
    predicted_quantity = models.IntegerField()
    confidence_lower = models.IntegerField()
    confidence_upper = models.IntegerField()
    
    actual_quantity = models.IntegerField(null=True, blank=True)
    model_used = models.CharField(max_length=100)
    accuracy_score = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_demand_forecasts'
        unique_together = ['product', 'forecast_date']

class DynamicPrice(models.Model):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    predicted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    demand_score = models.FloatField(default=0)
    competitor_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    inventory_level = models.IntegerField()
    
    strategy_used = models.CharField(max_length=100)
    update_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_dynamic_prices'
        ordering = ['-created_at']

class CustomerSegment(models.Model):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Segment criteria
    criteria = models.JSONField()
    segment_size = models.IntegerField(default=0)
    
    # Characteristics
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_frequency = models.FloatField(default=0)
    average_lifetime = models.IntegerField(default=0)  # Days
    
    # AI Data
    cluster_id = models.IntegerField()
    cluster_center = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_customer_segments'

class FraudDetection(models.Model):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    
    risk_score = models.FloatField()
    risk_level = models.CharField(max_length=20)  # low, medium, high, critical
    
    factors = models.JSONField()  # List of risk factors
    recommendations = models.JSONField(default=list)
    
    is_flagged = models.BooleanField(default=False)
    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_fraud_detections'

class AIContent(models.Model):
    CONTENT_TYPES = [
        ('product_description', 'Product Description'),
        ('seo_meta', 'SEO Meta'),
        ('blog_post', 'Blog Post'),
        ('email', 'Email'),
        ('social_media', 'Social Media'),
        ('product_title', 'Product Title'),
    ]
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPES)
    source_data = models.JSONField()  # Input data for generation
    generated_content = models.TextField()
    ai_metadata = models.JSONField(default=dict)
    
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_contents'