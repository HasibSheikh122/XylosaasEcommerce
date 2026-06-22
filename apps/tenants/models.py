# apps/tenants/models.py
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Tenant(TenantMixin):
    name = models.CharField(max_length=100)
    store_name = models.CharField(max_length=100)
    subdomain = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Subscription related
    plan = models.ForeignKey('subscriptions.Plan', on_delete=models.SET_NULL, null=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    is_trial = models.BooleanField(default=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    
    # Store settings
    logo = models.ImageField(upload_to='store_logos/', null=True, blank=True)
    favicon = models.ImageField(upload_to='favicons/', null=True, blank=True)
    custom_domain = models.CharField(max_length=255, null=True, blank=True)
    
    # Limits
    max_products = models.IntegerField(default=100)
    max_staff = models.IntegerField(default=5)
    max_orders_per_month = models.IntegerField(default=500)
    
    # AI Features
    ai_enabled = models.BooleanField(default=False)
    ai_features = models.JSONField(default=list)  # List of enabled AI features
    
    class Meta:
        db_table = 'tenants'
    
    def __str__(self):
        return self.store_name

class Domain(DomainMixin):
    domain = models.CharField(max_length=253, unique=True)
    is_primary = models.BooleanField(default=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='domains')
    
    def __str__(self):
        return self.domain