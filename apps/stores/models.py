from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class StoreSettings(models.Model):
    """Store configuration settings"""
    
    CURRENCY_CHOICES = [
        ('BDT', 'Bangladeshi Taka'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('INR', 'Indian Rupee'),
    ]
    
    TIMEZONE_CHOICES = [
        ('Asia/Dhaka', 'Asia/Dhaka'),
        ('Asia/Kolkata', 'Asia/Kolkata'),
        ('UTC', 'UTC'),
        ('America/New_York', 'America/New_York'),
        ('Europe/London', 'Europe/London'),
    ]
    
    tenant = models.OneToOneField('tenants.Tenant', on_delete=models.CASCADE)
    
    # General settings
    store_name = models.CharField(max_length=100)
    store_tagline = models.CharField(max_length=200, blank=True)
    store_description = models.TextField(blank=True)
    store_logo = models.ImageField(upload_to='stores/logos/', null=True, blank=True)
    store_favicon = models.ImageField(upload_to='stores/favicons/', null=True, blank=True)
    store_cover_image = models.ImageField(upload_to='stores/covers/', null=True, blank=True)
    
    # Branding
    primary_color = models.CharField(max_length=7, default='#007bff')
    secondary_color = models.CharField(max_length=7, default='#6c757d')
    accent_color = models.CharField(max_length=7, default='#28a745')
    font_family = models.CharField(max_length=100, default='Arial, sans-serif')
    
    # Contact info
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    contact_address = models.JSONField(default=dict, blank=True)
    
    # Social media
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    
    # Location and regional settings
    country = models.CharField(max_length=100, default='Bangladesh')
    city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, default='Asia/Dhaka')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='BDT')
    currency_symbol = models.CharField(max_length=5, default='৳')
    
    # Domain settings
    custom_domain = models.CharField(max_length=255, blank=True)
    subdomain = models.CharField(max_length=100)
    
    # SEO settings
    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.TextField(blank=True)
    seo_keywords = models.CharField(max_length=500, blank=True)
    seo_robots = models.CharField(max_length=100, default='index, follow')
    
    # Business hours
    business_hours = models.JSONField(default=dict, blank=True)
    
    # Checkout settings
    enable_guest_checkout = models.BooleanField(default=True)
    require_account_for_checkout = models.BooleanField(default=False)
    enable_cod = models.BooleanField(default=True)
    enable_online_payment = models.BooleanField(default=True)
    
    # Policies
    privacy_policy = models.TextField(blank=True)
    terms_conditions = models.TextField(blank=True)
    return_policy = models.TextField(blank=True)
    shipping_policy = models.TextField(blank=True)
    
    # Notification settings
    email_notifications = models.JSONField(default=dict, blank=True)
    sms_notifications = models.JSONField(default=dict, blank=True)
    push_notifications = models.JSONField(default=dict, blank=True)
    
    # Theme settings
    theme = models.CharField(max_length=50, default='default')
    theme_config = models.JSONField(default=dict, blank=True)
    custom_css = models.TextField(blank=True)
    custom_js = models.TextField(blank=True)
    
    # Advanced settings
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(blank=True)
    allow_adult_products = models.BooleanField(default=False)
    
    # Analytics tracking
    google_analytics_id = models.CharField(max_length=50, blank=True)
    facebook_pixel_id = models.CharField(max_length=50, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stores_settings'
    
    def __str__(self):
        return f"Settings for {self.store_name}"

class StoreStaff(models.Model):
    """Store staff members and roles"""
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Store Manager'),
        ('staff', 'Staff'),
        ('cashier', 'Cashier'),
        ('delivery_agent', 'Delivery Agent'),
        ('support', 'Customer Support'),
    ]
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    permissions = models.JSONField(default=list, blank=True)
    
    # Staff info
    employee_id = models.CharField(max_length=50, blank=True)
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    
    # Contact
    phone = models.CharField(max_length=20, blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    
    # Employment
    hire_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, default='active')
    
    # Schedule
    work_schedule = models.JSONField(default=dict, blank=True)
    
    # Shift
    shift_start = models.TimeField(null=True, blank=True)
    shift_end = models.TimeField(null=True, blank=True)
    
    # Commission
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    total_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Notes
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stores_staff'
        unique_together = ['tenant', 'user']
    
    def __str__(self):
        return f"{self.user.email} - {self.get_role_display()}"

class StoreCategory(models.Model):
    """Store categories for products"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    image = models.ImageField(upload_to='store_categories/', null=True, blank=True)
    
    # Display settings
    display_order = models.IntegerField(default=0)
    show_in_nav = models.BooleanField(default=True)
    show_on_homepage = models.BooleanField(default=False)
    
    # SEO
    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.TextField(blank=True)
    seo_keywords = models.CharField(max_length=500, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stores_category'
        ordering = ['display_order', 'name']
        unique_together = ['tenant', 'slug']
    
    def __str__(self):
        return self.name
    
    # === এই নিচে মেথডটি বসিয়ে দিন ===
    def save(self, *args, **kwargs):
        from django.utils.text import slugify # ইমপোর্টটি এখানে বা ফাইলের একদম উপরে দিতে পারেন
        if not self.slug:
            self.slug = slugify(self.name) # নামের ওপর ভিত্তি করে স্লাগ বানাবে
        super().save(*args, **kwargs)

class StorePage(models.Model):
    """Custom pages for the store"""
    
    PAGE_TYPES = [
        ('about', 'About Us'),
        ('contact', 'Contact Us'),
        ('faq', 'FAQ'),
        ('privacy', 'Privacy Policy'),
        ('terms', 'Terms and Conditions'),
        ('return', 'Return Policy'),
        ('shipping', 'Shipping Policy'),
        ('custom', 'Custom Page'),
    ]
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    page_type = models.CharField(max_length=20, choices=PAGE_TYPES, default='custom')
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255)
    content = models.TextField()
    excerpt = models.TextField(blank=True)
    
    # Featured image
    featured_image = models.ImageField(upload_to='pages/', null=True, blank=True)
    
    # SEO
    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.TextField(blank=True)
    seo_keywords = models.CharField(max_length=500, blank=True)
    
    # Display
    show_in_footer = models.BooleanField(default=False)
    show_in_header = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    
    # Status
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    meta_data = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stores_page'
        ordering = ['display_order', 'title']
        unique_together = ['tenant', 'slug']
    
    def __str__(self):
        return self.title
    
     # === এই নিচে মেথডটি বসিয়ে দিন ===
    def save(self, *args, **kwargs):
        from django.utils.text import slugify # ইমপোর্টটি এখানে বা ফাইলের একদম উপরে দিতে পারেন
        if not self.slug:
            self.slug = slugify(self.title) # শিরোনামের ওপর ভিত্তি করে স্লাগ বানাবে
        super().save(*args, **kwargs)

class StoreNotification(models.Model):
    """Store notifications and announcements"""
    
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('promotion', 'Promotion'),
        ('update', 'Update'),
        ('maintenance', 'Maintenance'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.URLField(blank=True)
    link_text = models.CharField(max_length=100, blank=True)
    
    # Target audience
    target_roles = models.JSONField(default=list, blank=True)
    target_customers = models.ManyToManyField('customers.Customer', blank=True)
    
    # Display settings
    show_to_all = models.BooleanField(default=True)
    is_popup = models.BooleanField(default=False)
    dismissible = models.BooleanField(default=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_read = models.BooleanField(default=False)
    read_by = models.ManyToManyField('users.User', blank=True, related_name='read_notifications')
    
    # Schedule
    publish_from = models.DateTimeField()
    publish_to = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stores_notification'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title