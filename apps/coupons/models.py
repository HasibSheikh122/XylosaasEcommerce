from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Coupon(models.Model):
    """কুপন ও ডিসকাউন্ট মডেল"""
    
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
    
    # বেসিক তথ্য
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # ডিসকাউন্ট কনফিগারেশন
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    max_discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Buy X Get Y কনফিগারেশন
    buy_quantity = models.IntegerField(null=True, blank=True)
    get_quantity = models.IntegerField(null=True, blank=True)
    get_discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # পণ্য ও ক্যাটাগরি সীমাবদ্ধতা
    apply_to = models.CharField(max_length=30, choices=APPLY_TO_CHOICES, default='all_products')
    applicable_categories = models.ManyToManyField('products.Category', blank=True)
    applicable_products = models.ManyToManyField('products.Product', blank=True)
    excluded_products = models.ManyToManyField('products.Product', blank=True, related_name='excluded_coupons')
    
    # ব্যবহার সীমা
    usage_limit = models.IntegerField(null=True, blank=True)
    per_user_limit = models.IntegerField(default=1)
    used_count = models.IntegerField(default=0)
    
    # সময়সীমা
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    
    # অর্ডারের টাকার পরিমাণ সীমা
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
    
    # গ্রাহক সীমাবদ্ধতা
    new_customers_only = models.BooleanField(default=False)
    first_order_only = models.BooleanField(default=False)
    applicable_customer_segments = models.JSONField(default=list, blank=True)
    
    # স্ট্যাটাস ও ভিজিবিলিটি
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    show_on_checkout = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    can_combine = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    
    # মেটাডাটা
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
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
    
    def is_valid(self, cart_total=None, customer=None, product_ids=None):
        """কুপন ভ্যালিডেশন লজিক (প্রোডাক্ট লিমিট, কাস্টমার লিমিট ও ফার্স্ট অর্ডার যাচাই)"""
        if self.status != 'active':
            return False, "কুপনটি সক্রিয় নয়।"
        
        now = timezone.now()
        if now < self.valid_from:
            return False, "কুপনটির মেয়াদ এখনও শুরু হয়নি।"
        if now > self.valid_to:
            return False, "কুপনটির মেয়াদ শেষ হয়ে গেছে।"
        
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False, "কুপন ব্যবহারের সর্বমোট সীমা শেষ।"
        
        # ১. নতুন কাস্টমার ও ফার্স্ট অর্ডার ভ্যালিডেশন
        if customer:
            if (self.first_order_only or self.new_customers_only) and customer.total_orders > 0:
                return False, "এই কুপনটি শুধুমাত্র নতুন গ্রাহকদের প্রথম অর্ডারের জন্য প্রযোজ্য।"
            
            # প্রতি কাস্টমারের ব্যবহার সীমা (যেমন: ১ বার)
            if self.per_user_limit > 0:
                used_count = CouponUsage.objects.filter(coupon=self, customer=customer).count()
                if used_count >= self.per_user_limit:
                    return False, "আপনি ইতিমধ্যে এই কুপনটি ব্যবহার করে ফেলেছেন।"

        # ২. মিনিমাম ও ম্যাক্সিমাম অর্ডার ভ্যালু ভ্যালিডেশন
        if cart_total is not None:
            if self.minimum_order_amount and cart_total < self.minimum_order_amount:
                return False, f"ন্যূনতম ৳{self.minimum_order_amount:,.0f} টাকার অর্ডারে কুপনটি প্রযোজ্য।"
            if self.maximum_order_amount and cart_total > self.maximum_order_amount:
                return False, f"সর্বোচ্চ ৳{self.maximum_order_amount:,.0f} টাকার অর্ডারে কুপনটি প্রযোজ্য।"

        # ৩. নির্দিষ্ট প্রোডাক্ট সীমাবদ্ধতা ভ্যালিডেশন
        if product_ids:
            # এক্সক্লুডেড প্রোডাক্ট চেক
            excluded_ids = set(self.excluded_products.values_list('id', flat=True))
            if excluded_ids and all(pid in excluded_ids for pid in product_ids):
                return False, "আপনার কার্টের পণ্যগুলোর ওপর এই কুপন প্রযোজ্য নয়।"

            # স্পেসিফিক প্রোডাক্ট রুল
            if self.apply_to == 'specific_products':
                applicable_ids = set(self.applicable_products.values_list('id', flat=True))
                if not any(pid in applicable_ids for pid in product_ids):
                    return False, "নির্বাচিত পণ্যের জন্য কুপনটি প্রযোজ্য নয়।"

        return True, "কুপন কার্যকর।"
    
    def calculate_discount(self, cart_total, product_ids=None, items=None):
        """ডিসকাউন্টের পরিমাণ হিসাব"""
        cart_total = Decimal(str(cart_total))

        if self.discount_type == 'percentage':
            discount = cart_total * (self.discount_value / Decimal('100.00'))
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return discount
        
        elif self.discount_type == 'fixed':
            return min(self.discount_value, cart_total)
        
        elif self.discount_type == 'free_shipping':
            return Decimal('0.00')
        
        elif self.discount_type == 'buy_x_get_y':
            if items and self.buy_quantity and self.get_quantity:
                eligible_items = self._get_eligible_items(items)
                if eligible_items:
                    eligible_items.sort(key=lambda x: x.price)
                    free_items = eligible_items[:self.get_quantity]
                    return sum([item.price for item in free_items])
            return Decimal('0.00')
        
        return Decimal('0.00')
    
    def _get_eligible_items(self, items):
        """Buy X Get Y এর জন্য যোগ্য পণ্য ফিল্টার"""
        if self.apply_to == 'all_products':
            return items
        elif self.apply_to == 'specific_products':
            return [item for item in items if item.product in self.applicable_products.all()]
        elif self.apply_to == 'specific_categories':
            return [item for item in items if item.product.category in self.applicable_categories.all()]
        return []


class CouponUsage(models.Model):
    """কুপন ব্যবহারের হিস্ট্রি মডেল"""
    
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE)
    
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    original_amount = models.DecimalField(max_digits=10, decimal_places=2)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    is_valid = models.BooleanField(default=True)
    is_refunded = models.BooleanField(default=False)
    
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
    """উন্নত কুপন রুলস (দিন, সময়, কাস্টমার গ্রুপ ইত্যাদি)"""
    
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
    rule_value = models.JSONField()
    is_required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'coupons_rule'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.coupon.code} - {self.get_rule_type_display()}"


class CouponCategory(models.Model):
    """কুপন ক্যাটাগরি মডেল"""
    
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