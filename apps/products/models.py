# apps/products/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify


class Category(models.Model):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # UI Icons & Display
    icon = models.CharField(
        max_length=50, 
        blank=True, 
        help_text="Emoji বা Lucide icon name (যেমন: 🥦, 🍎, 🥛, 🍞)"
    )
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    display_order = models.IntegerField(default=0)
    show_on_homepage = models.BooleanField(default=True, help_text="হোমপেজ বাবল গ্রিডে দেখাবে কি না")
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products_category'
        ordering = ['display_order', 'name']
        unique_together = ['tenant', 'slug']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    categories = models.ManyToManyField(Category, related_name='products', blank=True)
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, blank=True)
    description = models.TextField(blank=True)
    
    # Grocery Unit / Packaging (e.g., 500 g, 1 kg, 250 ml, 1 pc)
    unit = models.CharField(
        max_length=50, 
        default="1 pc", 
        help_text="কার্ডে টাইটেলের নিচে দেখাবে (যেমন: 500 g, 1 kg, 1 bunch)"
    )
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="বর্তমান বিক্রয়মূল্য")
    compare_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="আগের কাটা দাম (স্ট্রাইকথ্রু প্রাইস)"
    )
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Badge / Offer Tag
    custom_badge = models.CharField(
        max_length=50, 
        blank=True, 
        help_text="যেমন: Organic, New. ফাঁকা রাখলে স্বয়ংক্রিয় ডিসকাউন্ট % দেখাবে"
    )
    
    # Ratings & Reviews (UI-এর ★ 4.9)
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        default=5.0, 
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)]
    )
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Inventory
    sku = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=100, blank=True)
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)
    
    # Attributes
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    dimensions = models.JSONField(null=True, blank=True)  # {length, width, height}
    variants = models.JSONField(default=list, null=True, blank=True)  # {size, color, material}
    
    # Media
    images = models.JSONField(default=list, null=True, blank=True)  # Fallback image URLs
    video_url = models.URLField(null=True, blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Homepage Section Toggles
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Featured Products সেকশনে দেখাবে")
    is_bestseller = models.BooleanField(default=False, help_text="Best Seller Products সেকশনে দেখাবে")
    is_deal_of_day = models.BooleanField(default=False, help_text="Deals of the Day সেকশনে দেখাবে")
    is_digital = models.BooleanField(default=False)
    
    # AI Data
    ai_embedding = models.JSONField(null=True, blank=True)
    ai_metadata = models.JSONField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products_product'
        ordering = ['-created_at']
        unique_together = ['tenant', 'sku']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def discount_percentage(self) -> int:
        """হিসাব করে ডিসকাউন্ট পার্সেন্টেজ বের করবে (যেমন: 20% off)"""
        if self.compare_price and self.compare_price > self.price:
            discount = ((self.compare_price - self.price) / self.compare_price) * 100
            return int(round(discount))
        return 0

    @property
    def primary_image_url(self):
        """প্রাইমারি ইমেজের URL রিটার্ন করবে"""
        primary = self.product_images.filter(is_primary=True).first()
        if primary and primary.image:
            return primary.image.url
        first_img = self.product_images.first()
        if first_img and first_img.image:
            return first_img.image.url
        if self.images and len(self.images) > 0:
            return self.images[0]
        return None

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'products_product_image'
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Image for {self.product.name}"