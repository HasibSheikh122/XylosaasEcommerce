from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class Coupon(models.Model):
    """Coupon/Discount code model"""
    
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('free_shipping', 'Free Shipping'),
        ('buy_x_get_y', 'Buy X Get Y'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('paused', 'Paused'),
        ('used_up', 'Used Up'),
    ]
    
    APPLY_TO_CHOICES = [
        ('all_products', 'All Products'),
        ('specific_categories', 'Specific Categories'),
        ('specific_products', 'Specific Products'),
    ]
    
    # Basic info
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Discount details
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # For percentage discount
    max_discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # For buy_x_get_y
    buy_quantity = models.IntegerField(null=True, blank=True)
    get_quantity = models.IntegerField(null=True, blank=True)
    get_discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Apply to
    apply_to = models.CharField(max_length=30, choices=APPLY_TO_CHOICES, default='all_products')
    applicable_categories = models.ManyToManyField('products.Category', blank=True)
    applicable_products = models.ManyToManyField('products.Product', blank=True)
    excluded_products = models.ManyToManyField('products.Product', blank=True, related_name='excluded_coupons')
    
    # Usage limits
    usage_limit = models.IntegerField(null=True, blank=True)  # Total uses allowed
    per_user_limit = models.IntegerField(default=1)  # Uses per customer
    used_count = models.IntegerField(default=0)
    
    # Time limits
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    
    # Order limits
    minimum_order_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    maximum_order_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Customer limits
    new_customers_only = models.BooleanField(default=False)
    first_order_only = models.BooleanField(default=False)
    applicable_customer_segments = models.JSONField(default=list, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Display
    show_on_checkout = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    
    # Stacking
    can_combine = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'coupons_coupon'
        ordering = ['-priority', 'code']
        indexes = [
            models.Index(fields=['tenant', 'code']),
            models.Index(fields=['tenant', 'status', 'valid_from', 'valid_to']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.get_discount_type_display()}"
    
    def is_valid(self, cart_total=None, customer=None):
        """Check if coupon is valid"""
        from django.utils import timezone
        
        # Check status
        if self.status != 'active':
            return False, "Coupon is not active"
        
        # Check time
        now = timezone.now()
        if now < self.valid_from:
            return False, "Coupon not yet valid"
        if now > self.valid_to:
            return False, "Coupon has expired"
        
        # Check usage limit
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False, "Coupon usage limit reached"
        
        # Check order amount
        if cart_total:
            if self.minimum_order_amount and cart_total < self.minimum_order_amount:
                return False, f"Minimum order amount of {self.minimum_order_amount} required"
            if self.maximum_order_amount and cart_total > self.maximum_order_amount:
                return False, f"Maximum order amount of {self.maximum_order_amount} exceeded"
        
        # Check customer
        if customer and self.first_order_only:
            if customer.total_orders > 0:
                return False, "This coupon is for first order only"
        
        # Check if customer already used this coupon
        if customer and self.per_user_limit > 0:
            used_count = CouponUsage.objects.filter(
                coupon=self,
                customer=customer
            ).count()
            if used_count >= self.per_user_limit:
                return False, "You have already used this coupon"
        
        return True, "Coupon is valid"
    
    def calculate_discount(self, cart_total, items=None):
        """Calculate discount amount"""
        if self.discount_type == 'percentage':
            discount = cart_total * (self.discount_value / 100)
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return discount
        
        elif self.discount_type == 'fixed':
            return min(self.discount_value, cart_total)
        
        elif self.discount_type == 'free_shipping':
            return 0  # Handled separately
        
        elif self.discount_type == 'buy_x_get_y':
            if items and self.buy_quantity and self.get_quantity:
                # Calculate discount based on buy x get y logic
                eligible_items = self._get_eligible_items(items)
                if eligible_items:
                    # Sort by price (cheapest free)
                    eligible_items.sort(key=lambda x: x.price)
                    free_items = eligible_items[:self.get_quantity]
                    return sum([item.price for item in free_items])
            return 0
        
        return 0
    
    def _get_eligible_items(self, items):
        """Get items eligible for buy_x_get_y"""
        if self.apply_to == 'all_products':
            return items
        elif self.apply_to == 'specific_products':
            return [item for item in items if item.product in self.applicable_products.all()]
        elif self.apply_to == 'specific_categories':
            return [item for item in items if item.product.category in self.applicable_categories.all()]
        return []

class CouponUsage(models.Model):
    """Track coupon usage"""
    
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE)
    
    # Discount applied
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    original_amount = models.DecimalField(max_digits=10, decimal_places=2)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    is_valid = models.BooleanField(default=True)
    is_refunded = models.BooleanField(default=False)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'coupons_usage'
        ordering = ['-used_at']
        unique_together = ['coupon', 'order']
    
    def __str__(self):
        return f"{self.coupon.code} - {self.order.order_number}"

class CouponRule(models.Model):
    """Advanced coupon rules"""
    
    RULE_TYPES = [
        ('day_of_week', 'Day of Week'),
        ('time_of_day', 'Time of Day'),
        ('customer_group', 'Customer Group'),
        ('cart_quantity', 'Cart Quantity'),
        ('cart_value', 'Cart Value'),
        ('product_count', 'Product Count'),
    ]
    
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='rules')
    
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    rule_value = models.JSONField()  # Store rule parameters
    
    is_required = models.BooleanField(default=True)  # Must meet this rule
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'coupons_rule'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.coupon.code} - {self.get_rule_type_display()}"

class CouponCategory(models.Model):
    """Coupon categories for organization"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'coupons_category'
        ordering = ['name']
    
    def __str__(self):
        return self.name