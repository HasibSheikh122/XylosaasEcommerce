# apps/subscriptions/models.py
from django.db import models

class Plan(models.Model):
    PLAN_TYPES = [
        ('starter', 'Starter'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    name = models.CharField(max_length=50, choices=PLAN_TYPES)
    display_name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Features
    max_products = models.IntegerField()
    max_staff = models.IntegerField()
    max_orders_per_month = models.IntegerField()
    custom_domain = models.BooleanField(default=False)
    
    # AI Features
    ai_recommendation = models.BooleanField(default=False)
    ai_search = models.BooleanField(default=False)
    ai_chatbot = models.BooleanField(default=False)
    ai_analytics = models.BooleanField(default=False)
    ai_demand_forecast = models.BooleanField(default=False)
    ai_dynamic_pricing = models.BooleanField(default=False)
    ai_customer_segmentation = models.BooleanField(default=False)
    ai_churn_prediction = models.BooleanField(default=False)
    ai_fraud_detection = models.BooleanField(default=False)
    ai_content_generator = models.BooleanField(default=False)
    
    # Pricing
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    yearly_price = models.DecimalField(max_digits=10, decimal_places=2)
    setup_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plans'
    
    def __str__(self):
        return self.display_name

class Subscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('trial', 'Trial'),
        ('expired', 'Expired'),
    ]
    
    tenant = models.OneToOneField('tenants.Tenant', on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    
    # Dates
    trial_start = models.DateTimeField()
    trial_end = models.DateTimeField()
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    canceled_at = models.DateTimeField(null=True, blank=True)
    
    # Payment info
    payment_provider = models.CharField(max_length=50, null=True, blank=True)
    payment_provider_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions'
    
    def __str__(self):
        return f"{self.tenant.store_name} - {self.plan.display_name}"