# apps/customers/models.py
from django.db import models
from django.utils import timezone


class Customer(models.Model):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    user = models.OneToOneField('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    # Addresses
    default_shipping_address = models.JSONField(null=True, blank=True)
    default_billing_address = models.JSONField(null=True, blank=True)
    saved_addresses = models.JSONField(default=list)
    
    # Customer data
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_order_date = models.DateTimeField(null=True, blank=True)
    
    # Marketing
    email_opt_in = models.BooleanField(default=True)
    sms_opt_in = models.BooleanField(default=False)
    
    # AI Data
    customer_segment = models.CharField(max_length=50, blank=True)
    lifetime_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    churn_risk = models.FloatField(default=0)
    
    # Metadata
    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customers_customer'
        unique_together = ['tenant', 'email']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.email

    @property
    def last_active(self):
        if self.user and self.user.last_login:
            return self.user.last_login
        return self.last_order_date or self.updated_at or self.created_at