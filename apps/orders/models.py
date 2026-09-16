import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True, blank=True)

    order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Amounts
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    # Addresses
    shipping_address = models.JSONField(default=dict)
    billing_address = models.JSONField(default=dict)

    # Shipping Info
    shipping_method = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # Payment
    payment_method = models.CharField(max_length=50, default='cod')
    payment_status = models.CharField(max_length=20, default='pending')
    payment_id = models.CharField(max_length=255, blank=True)

    # Metadata
    notes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders_order'
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True)

    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=50)
    variant_data = models.JSONField(null=True, blank=True)

    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'orders_order_item'

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


class Cart(models.Model):
    CART_STATUS = [
        ('active', 'Active'),
        ('abandoned', 'Abandoned'),
        ('converted', 'Converted to Order'),
        ('expired', 'Expired'),
    ]

    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True, blank=True)

    session_id = models.CharField(max_length=255, blank=True, null=True)
    cart_token = models.CharField(max_length=255, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=CART_STATUS, default='active')

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    coupon_code = models.CharField(max_length=50, blank=True)
    coupon_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    shipping_method = models.CharField(max_length=100, blank=True)
    shipping_address = models.JSONField(default=dict, blank=True)
    billing_address = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders_cart'
        ordering = ['-created_at']

    def __str__(self):
        return f"Cart #{self.id} ({self.cart_token[:8]})"

    def calculate_totals(self):
        items = self.items.all()
        if not items.exists():
            self.subtotal = Decimal('0.00')
            self.tax_total = Decimal('0.00')
            self.shipping_total = Decimal('0.00')
            self.discount_total = Decimal('0.00')
            self.grand_total = Decimal('0.00')
            self.save()
            return

        subtotal = sum((item.unit_price * item.quantity) for item in items)
        tax_total = sum(item.get_tax_amount() for item in items)
        shipping_total = self.calculate_shipping()
        discount_total = self.coupon_discount

        self.subtotal = subtotal
        self.tax_total = tax_total
        self.shipping_total = shipping_total
        self.discount_total = discount_total
        self.grand_total = max(Decimal('0.00'), subtotal + tax_total + shipping_total - discount_total)
        self.save()

    def calculate_shipping(self):
        total_weight = sum((item.weight_per_unit * item.quantity) for item in self.items.all())
        if total_weight <= Decimal('1.00'):
            return Decimal('60.00')
        elif total_weight <= Decimal('5.00'):
            return Decimal('100.00')
        return Decimal('150.00')

    def apply_coupon(self, coupon_code):
        from apps.coupons.models import Coupon
        try:
            coupon = Coupon.objects.get(
                tenant=self.tenant,
                code__iexact=coupon_code.strip(),
                status='active'
            )
            is_valid, message = coupon.is_valid(self.subtotal, self.customer)
            if not is_valid:
                return False, message

            discount = coupon.calculate_discount(self.subtotal)
            self.coupon_code = coupon.code
            self.coupon_discount = discount
            self.calculate_totals()
            return True, f"কুপন সফলভাবে প্রয়োগ হয়েছে! আপনি ৳{discount} ছাড় পেয়েছেন।"
        except Coupon.DoesNotExist:
            return False, "কুপন কোডটি সঠিক নয়।"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)

    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=50)
    variant_data = models.JSONField(default=dict, blank=True)

    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    weight_per_unit = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders_cart_item'
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    def get_total_price(self):
        return self.unit_price * self.quantity

    def get_tax_amount(self):
        return (self.unit_price * self.quantity) * (self.tax_rate / Decimal('100.00'))


class Checkout(models.Model):
    CHECKOUT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHODS = [
        ('cod', 'Cash on Delivery'),
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('rocket', 'Rocket'),
        ('sslcommerz', 'SSLCommerz'),
        ('stripe', 'Stripe'),
    ]

    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, related_name='checkout')
    order = models.OneToOneField(Order, on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=20, choices=CHECKOUT_STATUS, default='pending')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default='cod')
    payment_status = models.CharField(max_length=50, default='pending')
    payment_id = models.CharField(max_length=255, blank=True)

    shipping_address = models.JSONField(default=dict)
    billing_address = models.JSONField(default=dict)
    shipping_method = models.CharField(max_length=100, default='Standard')
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=255)
    customer_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders_checkout'

    def __str__(self):
        return f"Checkout #{self.id} - {self.customer_name}"


class CheckoutLog(models.Model):
    checkout = models.ForeignKey(Checkout, on_delete=models.CASCADE, related_name='logs')
    log_type = models.CharField(max_length=20)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'orders_checkout_log'