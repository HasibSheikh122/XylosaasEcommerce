from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class PaymentGateway(models.Model):
    """Payment gateway configuration"""
    
    GATEWAY_TYPES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('sslcommerz', 'SSLCommerz'),
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('rocket', 'Rocket'),
    ]
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    gateway_type = models.CharField(max_length=20, choices=GATEWAY_TYPES)
    
    # Configuration
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # API Keys (encrypted in production)
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    api_username = models.CharField(max_length=100, blank=True)
    api_password = models.CharField(max_length=100, blank=True)
    
    # Gateway specific settings
    gateway_settings = models.JSONField(default=dict, blank=True)
    
    # Fees
    transaction_fee_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    transaction_fee_fixed = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments_gateway'
        unique_together = ['tenant', 'gateway_type']
        ordering = ['-is_default', 'gateway_type']
    
    def __str__(self):
        return f"{self.get_gateway_type_display()} - {self.tenant.store_name}"

class PaymentTransaction(models.Model):
    """Payment transaction record"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
        ('partial_refund', 'Partial Refund'),
        ('chargeback', 'Chargeback'),
        ('disputed', 'Disputed'),
    ]
    
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_banking', 'Mobile Banking'),
        ('digital_wallet', 'Digital Wallet'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('installment', 'Installment'),
    ]
    
    # Relationships
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True)
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.SET_NULL, null=True)
    
    # Transaction details
    transaction_id = models.CharField(max_length=255, unique=True)
    order_number = models.CharField(max_length=50, blank=True)
    invoice_number = models.CharField(max_length=50, blank=True)
    
    # Amounts
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='BDT')
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment info
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Gateway response
    gateway_transaction_id = models.CharField(max_length=255, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    gateway_error = models.TextField(blank=True)
    
    # Customer info
    customer_name = models.CharField(max_length=255, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    billing_address = models.JSONField(default=dict, blank=True)
    
    # Card info (partial)
    card_last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=50, blank=True)
    card_expiry = models.CharField(max_length=7, blank=True)
    
    # Refund info
    refund_status = models.CharField(max_length=20, blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refund_transaction_id = models.CharField(max_length=255, blank=True)
    refund_reason = models.TextField(blank=True)
    
    # IP and user agent
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'payments_transaction'
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'order']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['gateway_transaction_id']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.amount} {self.currency}"
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    def is_completed(self):
        return self.status == 'completed'
    
    def is_failed(self):
        return self.status == 'failed'
    
    def is_pending(self):
        return self.status == 'pending'

class PaymentSubscription(models.Model):
    """Subscription payment record"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    subscription = models.ForeignKey('subscriptions.Subscription', on_delete=models.CASCADE)
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True)
    
    # Subscription details
    plan_name = models.CharField(max_length=100)
    plan_price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_cycle = models.CharField(max_length=20)  # monthly, yearly
    
    # Payment details
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    
    # Period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Status
    status = models.CharField(max_length=20, default='active')
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'payments_subscription'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.tenant.store_name} - {self.plan_name} - {self.period_start}"

class PaymentRefund(models.Model):
    """Refund record"""
    
    REASON_CHOICES = [
        ('duplicate', 'Duplicate Payment'),
        ('fraud', 'Fraudulent Order'),
        ('customer_request', 'Customer Request'),
        ('product_issue', 'Product Issue'),
        ('shipping_issue', 'Shipping Issue'),
        ('other', 'Other'),
    ]
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.CASCADE)
    
    refund_transaction_id = models.CharField(max_length=255, unique=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    refund_reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    refund_reason_detail = models.TextField(blank=True)
    
    # Gateway response
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Status
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, default='pending')
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payments_refund'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund {self.refund_transaction_id} - {self.refund_amount}"

class PaymentLog(models.Model):
    """Payment log for debugging"""
    
    LOG_TYPES = [
        ('request', 'Request'),
        ('response', 'Response'),
        ('webhook', 'Webhook'),
        ('error', 'Error'),
        ('debug', 'Debug'),
    ]
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, null=True, blank=True)
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    log_data = models.JSONField()
    response_data = models.JSONField(default=dict, blank=True)
    
    error_message = models.TextField(blank=True)
    error_code = models.CharField(max_length=50, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments_log'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.log_type} - {self.created_at}"