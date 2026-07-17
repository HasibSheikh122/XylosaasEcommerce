# apps/orders/models.py
from django.db import models

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
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True)
    
    # Order info
    order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Customer info
    shipping_address = models.JSONField()
    billing_address = models.JSONField()
    
    # Shipping
    shipping_method = models.CharField(max_length=100)
    tracking_number = models.CharField(max_length=100, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Payment
    payment_method = models.CharField(max_length=50)
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
    
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'orders_order_item'


from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

# ==============================================================================
# 🛒 CART MODELS
# ==============================================================================

class Cart(models.Model):
    """Shopping Cart Model"""
    
    CART_STATUS = [
        ('active', 'Active'),
        ('abandoned', 'Abandoned'),
        ('converted', 'Converted to Order'),
        ('expired', 'Expired'),
    ]
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, null=True, blank=True)
    
    # Session/User tracking
    session_id = models.CharField(max_length=255, blank=True, null=True)
    cart_token = models.CharField(max_length=255, unique=True)
    
    # Cart status
    status = models.CharField(max_length=20, choices=CART_STATUS, default='active')
    
    # Cart totals (denormalized for performance)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Coupon/Discount
    coupon_code = models.CharField(max_length=50, blank=True)
    coupon_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Shipping info
    shipping_method = models.CharField(max_length=100, blank=True)
    shipping_address = models.JSONField(default=dict, blank=True)
    
    # Billing info
    billing_address = models.JSONField(default=dict, blank=True)
    
    # Customer notes
    notes = models.TextField(blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'orders_cart'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'customer']),
            models.Index(fields=['tenant', 'session_id']),
            models.Index(fields=['cart_token']),
            models.Index(fields=['tenant', 'status']),
        ]
    
    def __str__(self):
        return f"Cart #{self.id} - {self.customer or self.session_id}"
    
    def calculate_totals(self):
        """Calculate all cart totals"""
        items = self.items.all()
        
        if not items:
            self.subtotal = 0
            self.tax_total = 0
            self.shipping_total = 0
            self.discount_total = 0
            self.grand_total = 0
            self.save()
            return
        
        # Calculate subtotal
        subtotal = sum(item.get_total_price() for item in items)
        
        # Calculate tax (e.g., 15% VAT)
        tax_rate = Decimal('0.15')  # কাস্টমাইজ করতে পারেন
        tax_total = subtotal * tax_rate
        
        # Shipping cost
        shipping_total = self.calculate_shipping()
        
        # Discount
        discount_total = self.coupon_discount
        
        # Grand total
        grand_total = subtotal + tax_total + shipping_total - discount_total
        
        # Update cart totals
        self.subtotal = subtotal
        self.tax_total = tax_total
        self.shipping_total = shipping_total
        self.discount_total = discount_total
        self.grand_total = grand_total
        self.save()
        
        return {
            'subtotal': subtotal,
            'tax_total': tax_total,
            'shipping_total': shipping_total,
            'discount_total': discount_total,
            'grand_total': grand_total,
        }
    
    def calculate_shipping(self):
        """Calculate shipping cost"""
        # আপনার শিপিং লজিক এখানে
        total_weight = sum(item.get_total_weight() for item in self.items.all())
        
        if total_weight <= 1:
            return Decimal('50.00')
        elif total_weight <= 5:
            return Decimal('100.00')
        else:
            return Decimal('150.00')
    
    def get_total_items(self):
        """Get total number of items in cart"""
        return self.items.aggregate(models.Sum('quantity'))['quantity__sum'] or 0
    
    def get_total_weight(self):
        """Get total weight of all items"""
        return sum(item.get_total_weight() for item in self.items.all())
    
    def apply_coupon(self, coupon_code):
        """Apply coupon to cart"""
        from apps.coupons.models import Coupon
        
        try:
            coupon = Coupon.objects.get(
                tenant=self.tenant,
                code=coupon_code,
                status='active'
            )
            
            # Check if coupon is valid
            is_valid, message = coupon.is_valid(self.grand_total, self.customer)
            
            if not is_valid:
                return False, message
            
            # Calculate discount
            discount = coupon.calculate_discount(self.grand_total)
            self.coupon_code = coupon_code
            self.coupon_discount = discount
            self.calculate_totals()
            
            return True, f"Coupon applied! You saved {discount}"
            
        except Coupon.DoesNotExist:
            return False, "Invalid coupon code"
    
    def clear_cart(self):
        """Clear all items from cart"""
        self.items.all().delete()
        self.coupon_code = ''
        self.coupon_discount = 0
        self.calculate_totals()
    
    def to_order(self):
        """Convert cart to order"""
        from .models import Order
        
        # Create order from cart
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            order_number=self.generate_order_number(),
            status='pending',
            subtotal=self.subtotal,
            tax=self.tax_total,
            shipping_cost=self.shipping_total,
            discount=self.discount_total,
            total=self.grand_total,
            shipping_address=self.shipping_address,
            billing_address=self.billing_address,
            shipping_method=self.shipping_method,
            notes=self.notes,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )
        
        # Create order items from cart items
        for cart_item in self.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                product_sku=cart_item.product.sku,
                variant_data=cart_item.variant_data,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                total_price=cart_item.get_total_price(),
                tax=cart_item.get_tax_amount(),
            )
        
        # Update cart status
        self.status = 'converted'
        self.save()
        
        return order
    
    def generate_order_number(self):
        """Generate unique order number"""
        import uuid
        return f"ORD-{uuid.uuid4().hex[:10].upper()}"


class CartItem(models.Model):
    """Cart Item Model"""
    
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    
    # Product details (snapshot)
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=50)
    
    # Variant data
    variant_data = models.JSONField(default=dict, blank=True)
    
    # Quantity and pricing
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Item weight (for shipping)
    weight_per_unit = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Metadata
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'orders_cart_item'
        ordering = ['-added_at']
        unique_together = ['cart', 'product']  # একই প্রোডাক্ট একবারই যোগ করা যাবে
    
    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
    
    def get_total_price(self):
        """Get total price for this item"""
        return self.unit_price * self.quantity
    
    def get_tax_amount(self):
        """Get tax amount for this item"""
        return (self.unit_price * self.quantity) * (self.tax_rate / 100)
    
    def get_total_weight(self):
        """Get total weight for this item"""
        return self.weight_per_unit * self.quantity
    
    def update_quantity(self, new_quantity):
        """Update item quantity"""
        if new_quantity <= 0:
            self.delete()
            return True
        
        self.quantity = new_quantity
        self.save()
        self.cart.calculate_totals()
        return True


# ==============================================================================
# 📦 CHECKOUT MODELS
# ==============================================================================

class Checkout(models.Model):
    """Checkout Process Model"""
    
    CHECKOUT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('payment_waiting', 'Waiting for Payment'),
        ('payment_completed', 'Payment Completed'),
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
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, related_name='checkout')
    order = models.OneToOneField('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, null=True, blank=True)
    
    # Checkout status
    status = models.CharField(max_length=20, choices=CHECKOUT_STATUS, default='pending')
    
    # Payment info
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=50, default='pending')
    payment_id = models.CharField(max_length=255, blank=True)
    payment_gateway_response = models.JSONField(default=dict, blank=True)
    
    # Shipping info
    shipping_address = models.JSONField()
    billing_address = models.JSONField()
    shipping_method = models.CharField(max_length=100)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Customer info
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=255)
    customer_notes = models.TextField(blank=True)
    
    # Order totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Coupon
    coupon_code = models.CharField(max_length=50, blank=True)
    coupon_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Checkout steps
    current_step = models.IntegerField(default=1)  # 1: Cart, 2: Shipping, 3: Payment, 4: Confirmation
    completed_steps = models.JSONField(default=list, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'orders_checkout'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'customer']),
            models.Index(fields=['cart']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f"Checkout #{self.id} - {self.customer_name}"
    
    def process_payment(self):
        """Process payment based on payment method"""
        # Payment logic here
        # Return success/failure
        pass
    
    def complete_checkout(self):
        """Complete checkout process"""
        # Convert cart to order
        self.order = self.cart.to_order()
        self.status = 'completed'
        self.completed_at = models.DateTimeField(auto_now_add=True)
        self.save()
        
        # Update cart status
        self.cart.status = 'converted'
        self.cart.save()
        
        # Send confirmation email
        self.send_confirmation_email()
        
        return self.order
    
    def send_confirmation_email(self):
        """Send order confirmation email"""
        # Email sending logic
        pass
    
    def get_checkout_summary(self):
        """Get checkout summary"""
        return {
            'subtotal': self.subtotal,
            'tax': self.tax_total,
            'shipping': self.shipping_cost,
            'discount': self.discount_total,
            'total': self.grand_total,
            'items': [
                {
                    'name': item.product_name,
                    'quantity': item.quantity,
                    'price': item.unit_price,
                    'total': item.get_total_price()
                }
                for item in self.cart.items.all()
            ]
        }


class CheckoutLog(models.Model):
    """Checkout activity log"""
    
    LOG_TYPES = [
        ('view', 'Page View'),
        ('step', 'Step Change'),
        ('payment', 'Payment Event'),
        ('error', 'Error'),
        ('success', 'Success'),
    ]
    
    checkout = models.ForeignKey(Checkout, on_delete=models.CASCADE, related_name='logs')
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True, blank=True)
    
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    step = models.IntegerField(null=True, blank=True)
    
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'orders_checkout_log'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.log_type} - {self.checkout.id}"