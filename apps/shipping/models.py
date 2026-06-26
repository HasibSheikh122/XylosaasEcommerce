from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class ShippingZone(models.Model):
    """Shipping zones for different regions"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Regions covered
    countries = models.JSONField(default=list)  # List of country codes
    states = models.JSONField(default=list, blank=True)  # List of states/provinces
    cities = models.JSONField(default=list, blank=True)  # List of cities
    zip_codes = models.JSONField(default=list, blank=True)  # List of zip codes
    
    # Delivery time
    estimated_delivery_days_min = models.IntegerField(default=1)
    estimated_delivery_days_max = models.IntegerField(default=5)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Priority (lower number = higher priority)
    priority = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shipping_zone'
        ordering = ['priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.tenant.store_name})"
    
    def is_in_zone(self, address):
        """Check if address is in this zone"""
        # Check country
        if self.countries and address.get('country') not in self.countries:
            return False
        
        # Check state
        if self.states and address.get('state') not in self.states:
            return False
        
        # Check city
        if self.cities and address.get('city') not in self.cities:
            return False
        
        # Check zip code
        if self.zip_codes:
            zip_code = address.get('zip_code', '')
            if zip_code not in self.zip_codes:
                return False
        
        return True

class ShippingMethod(models.Model):
    """Shipping methods available"""
    
    METHOD_TYPES = [
        ('standard', 'Standard Shipping'),
        ('express', 'Express Shipping'),
        ('overnight', 'Overnight Shipping'),
        ('international', 'International Shipping'),
        ('local_delivery', 'Local Delivery'),
        ('pickup', 'Store Pickup'),
    ]
    carrier = models.ForeignKey('Carrier', on_delete=models.SET_NULL, null=True, blank=True, related_name='methods')
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    zones = models.ManyToManyField(ShippingZone, blank=True)
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    method_type = models.CharField(max_length=20, choices=METHOD_TYPES)
    
    # Pricing
    base_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_per_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_per_item = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    handling_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Free shipping threshold
    free_shipping_threshold = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Item limits
    max_weight_kg = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    max_items = models.IntegerField(null=True, blank=True)
    
    # Delivery time
    delivery_days_min = models.IntegerField(default=1)
    delivery_days_max = models.IntegerField(default=5)
    
    # Tracking
    tracking_url = models.URLField(blank=True)
    tracking_required = models.BooleanField(default=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    is_available_for_cod = models.BooleanField(default=True)
    
    # Priority
    priority = models.IntegerField(default=0)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shipping_method'
        ordering = ['priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_method_type_display()})"
    
    def calculate_cost(self, weight_kg, item_count, subtotal, address=None):
        """Calculate shipping cost"""
        cost = self.base_cost
        
        # Add weight cost
        if weight_kg and self.cost_per_kg:
            cost += weight_kg * self.cost_per_kg
        
        # Add item cost
        if item_count and self.cost_per_item:
            cost += item_count * self.cost_per_item
        
        # Check free shipping
        if self.free_shipping_threshold and subtotal >= self.free_shipping_threshold:
            return 0
        
        # Check weight limit
        if self.max_weight_kg and weight_kg > self.max_weight_kg:
            return None  # Not available for this order
        
        # Check item limit
        if self.max_items and item_count > self.max_items:
            return None  # Not available for this order
        
        return cost + self.handling_fee

class ShippingRate(models.Model):
    """Custom shipping rates for specific conditions"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    method = models.ForeignKey(ShippingMethod, on_delete=models.CASCADE)
    zone = models.ForeignKey(ShippingZone, on_delete=models.CASCADE)
    
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Conditions
    min_weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    max_weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_order_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Priority
    priority = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shipping_rate'
        ordering = ['priority']
    
    def __str__(self):
        return f"{self.method.name} - {self.zone.name} - {self.rate}"

class Shipment(models.Model):
    """Shipment tracking"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('delayed', 'Delayed'),
        ('returned', 'Returned'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    method = models.ForeignKey(ShippingMethod, on_delete=models.SET_NULL, null=True)
    
    shipment_number = models.CharField(max_length=100, unique=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    carrier_name = models.CharField(max_length=100, blank=True)
    carrier_service = models.CharField(max_length=100, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Addresses
    pickup_address = models.JSONField(default=dict, blank=True)
    delivery_address = models.JSONField(default=dict)
    
    # Dates
    expected_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Weight and dimensions
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    dimensions = models.JSONField(null=True, blank=True)  # {length, width, height}
    
    # Costs
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    insurance_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cod_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Tracking updates
    tracking_history = models.JSONField(default=list, blank=True)
    
    # Signature
    signature_required = models.BooleanField(default=False)
    signature_photo = models.ImageField(upload_to='shipments/signatures/', null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    delivery_notes = models.TextField(blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shipping_shipment'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tracking_number']),
        ]
    
    def __str__(self):
        return f"{self.shipment_number} - {self.order.order_number}"
    
    def add_tracking_update(self, status, description, location=None):
        """Add a tracking update"""
        update = {
            'status': status,
            'description': description,
            'location': location,
            'timestamp': timezone.now().isoformat()
        }
        self.tracking_history.append(update)
        self.status = status
        self.save()

class Carrier(models.Model):
    """Shipping carrier configuration"""
    
    CARRIER_TYPES = [
        ('fedex', 'FedEx'),
        ('ups', 'UPS'),
        ('dhl', 'DHL'),
        ('usps', 'USPS'),
        ('aramex', 'Aramex'),
        ('pathao', 'Pathao'),
        ('redx', 'RedX'),
        ('sundarban', 'Sundarban'),
        ('paperfly', 'Paperfly'),
        ('eco_courier', 'Eco Courier'),
        ('self', 'Self Delivery'),
        ('other', 'Other'),
    ]
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    carrier_type = models.CharField(max_length=20, choices=CARRIER_TYPES)
    
    # API Configuration
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    api_username = models.CharField(max_length=100, blank=True)
    api_password = models.CharField(max_length=100, blank=True)
    api_url = models.URLField(blank=True)
    
    # Tracking
    tracking_url_template = models.URLField(blank=True)
    tracking_api_url = models.URLField(blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Supported services
    supported_services = models.JSONField(default=list, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shipping_carrier'
        ordering = ['carrier_type']
    
    def __str__(self):
        return f"{self.get_carrier_type_display()} - {self.name}"
    
    def get_tracking_url(self, tracking_number):
        """Generate tracking URL"""
        if self.tracking_url_template:
            return self.tracking_url_template.replace('{tracking}', tracking_number)
        return None