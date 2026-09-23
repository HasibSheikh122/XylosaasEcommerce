from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify


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

    THEME_CHOICES = [
        ('grocery', 'Fresh Grocery (Default)'),
        ('fashion', 'Modern Fashion (Premium)'),
        ('electronics', 'Tech Gadgets (Premium)'),
        ('minimal', 'Minimalist Clean (Premium)'),
    ]
    
    tenant = models.OneToOneField('tenants.Tenant', on_delete=models.CASCADE)
    
    # General settings
    store_name = models.CharField(max_length=100)
    store_tagline = models.CharField(max_length=200, blank=True)
    store_description = models.TextField(blank=True)
    store_logo = models.ImageField(upload_to='stores/logos/', null=True, blank=True)
    store_favicon = models.ImageField(upload_to='stores/favicons/', null=True, blank=True)
    store_cover_image = models.ImageField(upload_to='stores/covers/', null=True, blank=True)

    # Top Announcement Bar (UI-এর হলুদ টপ বার)
    show_announcement_bar = models.BooleanField(default=True)
    announcement_text = models.CharField(
        max_length=255, 
        default="Sign up and GET 20% OFF for your first order!", 
        blank=True
    )
    announcement_phone = models.CharField(max_length=30, default="+880 1700-000000", blank=True)
    
    # Branding
    primary_color = models.CharField(max_length=7, default='#059669', help_text="Emerald Green (#059669)")
    secondary_color = models.CharField(max_length=7, default='#054E34', help_text="Dark Forest Green (#054E34)")
    accent_color = models.CharField(max_length=7, default='#F59E0B', help_text="Warm Amber (#F59E0B)")
    font_family = models.CharField(max_length=100, default='Inter, sans-serif')
    
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
    
    # Theme Marketplace & Configuration
    theme = models.CharField(max_length=50, choices=THEME_CHOICES, default='grocery')
    theme_config = models.JSONField(default=dict, blank=True, help_text="কাস্টমাইজড থিম ভ্যারিয়েবল ও স্টাইল")
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
        return f"Settings for {self.store_name} ({self.get_theme_display()})"


from django.db import models
from django.core.exceptions import ValidationError


class StoreBanner(models.Model):
    """Banners, Promos, Hero Carousel, and Deals of the Day"""
    
    BANNER_TYPES = [
        ('hero', 'Main Hero Banner (Max 3 for Free Tier)'),
        ('dual_promo', 'Dual Promo Card (Half Width)'),
        ('countdown', 'Countdown Discount (Summer Discount)'),
        ('deal_of_day', 'Deal of The Day (With Countdown Timer)'),
        ('weekly', 'Weekly Specials Banner (Deep Green)'),
        ('wide_offer', 'Wide Offer Strip (Above Best Sellers)'),
    ]

    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    banner_type = models.CharField(max_length=30, choices=BANNER_TYPES, default='hero')
    badge_title = models.CharField(max_length=60, default="Flat 20% Discount", blank=True)
    title = models.CharField(max_length=200, help_text="e.g., Purely Fresh Vegetables")
    subtitle = models.TextField(blank=True, help_text="ছোট বিবরণী বা ট্যাগলাইন")
    
    # ব্যানার ইমেজ (Hero ও Countdown-এর দুই পাশের ছবির জন্য)
    image = models.ImageField(upload_to='stores/banners/', null=True, blank=True, help_text="মূল ছবি / বাম পাশের ছবি")
    secondary_image = models.ImageField(upload_to='stores/banners/', null=True, blank=True, help_text="ডান পাশের ছবি (ঐচ্ছিক)")
    
    button_text = models.CharField(max_length=50, default="Shop Now")
    target_url = models.CharField(max_length=255, default="/products", blank=True)
    
    # কাউন্টডাউন টাইমার (Summer Discount / Deal of the Day এর জন্য)
    countdown_end = models.DateTimeField(null=True, blank=True, help_text="অফার শেষের ডেট ও টাইম")
    
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stores_banner'
        ordering = ['display_order', '-created_at']

    def clean(self):
        super().clean()

        # হিরো ব্যানারের জন্য সর্বোচ্চ ৩টির সীমা যাচাই
        if self.banner_type == 'hero' and self.is_active:
            tenant = getattr(self, 'tenant', None)
            if tenant:
                active_heroes = StoreBanner.objects.filter(
                    tenant=tenant,
                    banner_type='hero',
                    is_active=True
                )
                
                # এডিট করার সময় বর্তমান অবজেক্টকে বাদ রাখা
                if self.pk:
                    active_heroes = active_heroes.exclude(pk=self.pk)

                if active_heroes.count() >= 3:
                    raise ValidationError({
                        'banner_type': (
                            'আপনি সর্বোচ্চ ৩টি সক্রিয় হিরো ব্যানার ব্যবহার করতে পারবেন। '
                            'আরও ব্যানার বা কাস্টম ক্যারোসেল ডিজাইন যোগ করতে প্রিমিয়াম ব্যানার অ্যাড-অন ক্রয় করুন।'
                        )
                    })

    def save(self, *args, **kwargs):
        # অ্যাডমিন এবং API উভয় ক্ষেত্রেই clean() ভ্যালিডেশন নিশ্চিত করা
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_banner_type_display()} - {self.title}"


class StoreFAQ(models.Model):
    """Homepage FAQ Accordion"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    question = models.CharField(max_length=255)
    answer = models.TextField()
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stores_faq'
        ordering = ['display_order', 'id']

    def __str__(self):
        return self.question


class StoreTestimonial(models.Model):
    """Customer Testimonials and Reviews"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=120)
    designation = models.CharField(max_length=100, default="Verified Buyer", help_text="e.g., Housewife / Regular Customer")
    avatar = models.ImageField(upload_to='stores/testimonials/', null=True, blank=True)
    rating = models.PositiveSmallIntegerField(
        default=5, 
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    is_featured = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stores_testimonial'
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return f"{self.customer_name} ({self.rating}★)"


class StoreNewsletterSubscriber(models.Model):
    """Store Newsletter Leads"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    email = models.EmailField()
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stores_newsletter'
        unique_together = ['tenant', 'email']
        ordering = ['-subscribed_at']

    def __str__(self):
        return self.email


class StoreBlogPost(models.Model):
    """Our Latest News & Blogs section"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255)
    category_tag = models.CharField(max_length=60, default="Shopping Tips", help_text="যেমন: Seasonal Guide / Healthy Eating")
    author_name = models.CharField(max_length=100, default="Store Admin")
    cover_image = models.ImageField(upload_to='stores/blogs/', null=True, blank=True)
    summary = models.TextField(help_text="কার্ডে প্রদর্শিত সংক্ষিপ্ত অংশ")
    content = models.TextField(help_text="মূল ব্লগ কনটেন্ট")
    
    published_at = models.DateField(auto_now_add=True)
    is_published = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stores_blog'
        ordering = ['-published_at']
        unique_together = ['tenant', 'slug']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


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
    
    employee_id = models.CharField(max_length=50, blank=True)
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    
    phone = models.CharField(max_length=20, blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    
    hire_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, default='active')
    
    work_schedule = models.JSONField(default=dict, blank=True)
    shift_start = models.TimeField(null=True, blank=True)
    shift_end = models.TimeField(null=True, blank=True)
    
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    total_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
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
    icon = models.CharField(max_length=50, blank=True, help_text="Emoji বা Lucide icon name (যেমন: 🥦)")
    image = models.ImageField(upload_to='store_categories/', null=True, blank=True)
    
    display_order = models.IntegerField(default=0)
    show_in_nav = models.BooleanField(default=True)
    show_on_homepage = models.BooleanField(default=True)
    
    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.TextField(blank=True)
    seo_keywords = models.CharField(max_length=500, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stores_category'
        ordering = ['display_order', 'name']
        unique_together = ['tenant', 'slug']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


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
    
    featured_image = models.ImageField(upload_to='pages/', null=True, blank=True)
    
    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.TextField(blank=True)
    seo_keywords = models.CharField(max_length=500, blank=True)
    
    show_in_footer = models.BooleanField(default=False)
    show_in_header = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    
    meta_data = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stores_page'
        ordering = ['display_order', 'title']
        unique_together = ['tenant', 'slug']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


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
    
    target_roles = models.JSONField(default=list, blank=True)
    target_customers = models.ManyToManyField('customers.Customer', blank=True)
    
    show_to_all = models.BooleanField(default=True)
    is_popup = models.BooleanField(default=False)
    dismissible = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    is_read = models.BooleanField(default=False)
    read_by = models.ManyToManyField('users.User', blank=True, related_name='read_notifications')
    
    publish_from = models.DateTimeField()
    publish_to = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stores_notification'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


# apps/stores/models.py er niche jog korun:

class StoreThemeTemplate(models.Model):
    THEME_KEYS = (
        ('default', 'Modern Clean Grocery/Fashion'),
        ('classified_soft', 'Soft 3D Clay Classified'),
        ('neon_studio', 'Cyber Neon Dark Studio'),
    )
    theme_key = models.CharField(max_length=50, choices=THEME_KEYS, unique=True)
    name = models.CharField(max_length=100)
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    preview_image = models.ImageField(upload_to='theme_previews/', null=True, blank=True)
    preview_image_url = models.URLField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.theme_key})"


class TenantPurchasedTheme(models.Model):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='purchased_themes')
    theme = models.ForeignKey(StoreThemeTemplate, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('tenant', 'theme')

    def __str__(self):
        return f"{self.tenant} - {self.theme.name}"

from django.db import models

class StoreGalleryImage(models.Model):
    image = models.ImageField(upload_to="store_gallery/")

    def __str__(self):
        return f"Gallery Image #{self.id}"