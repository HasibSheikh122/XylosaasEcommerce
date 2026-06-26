from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Review(models.Model):
    """Product review"""
    
    RATING_CHOICES = [
        (1, '1 Star - Very Poor'),
        (2, '2 Stars - Poor'),
        (3, '3 Stars - Average'),
        (4, '4 Stars - Good'),
        (5, '5 Stars - Excellent'),
    ]
    
    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged'),
    ]
    
    # Relationships
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Review content
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    rating = models.IntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Media
    images = models.JSONField(default=list, blank=True)  # List of image URLs
    videos = models.JSONField(default=list, blank=True)  # List of video URLs
    
    # Verification
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    verification_date = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    verified_purchase = models.BooleanField(default=False)
    
    # Helpful votes
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    
    # Review metrics
    is_featured = models.BooleanField(default=False)
    is_anonymous = models.BooleanField(default=False)
    sentiment_score = models.FloatField(null=True, blank=True)  # AI sentiment analysis
    
    # Moderation
    moderation_status = models.CharField(max_length=20, default='pending')
    moderation_notes = models.TextField(blank=True)
    flagged_count = models.IntegerField(default=0)
    
    # SEO
    seo_meta_title = models.CharField(max_length=255, blank=True)
    seo_meta_description = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'reviews_review'
        ordering = ['-created_at']
        unique_together = ['product', 'customer']
        indexes = [
            models.Index(fields=['tenant', 'product', 'rating']),
            models.Index(fields=['tenant', 'verification_status']),
            models.Index(fields=['tenant', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.rating}★"
    
    def get_average_rating(self):
        """Get average rating for the product"""
        return Review.objects.filter(
            product=self.product,
            verification_status='verified'
        ).aggregate(models.Avg('rating'))['rating__avg']
    
    def get_rating_distribution(self):
        """Get rating distribution for the product"""
        ratings = {}
        for i in range(1, 6):
            ratings[i] = Review.objects.filter(
                product=self.product,
                rating=i,
                verification_status='verified'
            ).count()
        return ratings
    
    def mark_as_helpful(self):
        self.helpful_count += 1
        self.save(update_fields=['helpful_count'])
    
    def mark_as_not_helpful(self):
        self.not_helpful_count += 1
        self.save(update_fields=['not_helpful_count'])

class ReviewReply(models.Model):
    """Reply to a review"""
    
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='replies')
    
    # Reply content
    content = models.TextField()
    
    # Who replied
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    is_owner_reply = models.BooleanField(default=False)
    
    # Media
    attachments = models.JSONField(default=list, blank=True)
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews_reply'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Reply to {self.review}"

class ReviewReport(models.Model):
    """Report a review for moderation"""
    
    REPORT_REASONS = [
        ('inappropriate', 'Inappropriate Content'),
        ('fake_review', 'Fake Review'),
        ('offensive', 'Offensive Language'),
        ('spam', 'Spam'),
        ('copyright', 'Copyright Issue'),
        ('other', 'Other'),
    ]
    
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey('customers.Customer', on_delete=models.CASCADE)
    
    reason = models.CharField(max_length=50, choices=REPORT_REASONS)
    description = models.TextField()
    
    status = models.CharField(max_length=20, default='pending')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews_report'
        ordering = ['-created_at']
        unique_together = ['review', 'reported_by']
    
    def __str__(self):
        return f"{self.review} - {self.get_reason_display()}"

class ReviewPhoto(models.Model):
    """Review photos/videos"""
    
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='review_photos')
    
    # Media file
    media_file = models.ImageField(upload_to='reviews/photos/')
    media_type = models.CharField(max_length=20, default='image')  # image, video
    
    # Metadata
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    # AI Analysis
    ai_analysis = models.JSONField(default=dict, blank=True)  # Object detection, sentiment
    is_approved = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reviews_photo'
        ordering = ['order']
    
    def __str__(self):
        return f"Photo for {self.review}"

class ReviewAnalytics(models.Model):
    """Review analytics and metrics"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    
    # Metrics
    total_reviews = models.IntegerField(default=0)
    verified_reviews = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0)
    
    # Rating distribution
    rating_1_count = models.IntegerField(default=0)
    rating_2_count = models.IntegerField(default=0)
    rating_3_count = models.IntegerField(default=0)
    rating_4_count = models.IntegerField(default=0)
    rating_5_count = models.IntegerField(default=0)
    
    # Sentiment analysis
    positive_sentiment = models.IntegerField(default=0)
    neutral_sentiment = models.IntegerField(default=0)
    negative_sentiment = models.IntegerField(default=0)
    sentiment_score = models.FloatField(default=0)
    
    # Helpful metrics
    total_helpful_votes = models.IntegerField(default=0)
    total_not_helpful_votes = models.IntegerField(default=0)
    helpful_ratio = models.FloatField(default=0)
    
    # Time-based
    reviews_last_7_days = models.IntegerField(default=0)
    reviews_last_30_days = models.IntegerField(default=0)
    reviews_last_90_days = models.IntegerField(default=0)
    
    # Top keywords
    top_positive_keywords = models.JSONField(default=list, blank=True)
    top_negative_keywords = models.JSONField(default=list, blank=True)
    
    # Recent trends
    rating_trend = models.JSONField(default=dict, blank=True)  # Daily/Monthly trend
    
    # Updated at
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews_analytics'
        unique_together = ['tenant', 'product']
    
    def __str__(self):
        return f"{self.product.name} - {self.average_rating}★"
    
    def update_analytics(self):
        """Update all analytics for this product"""
        reviews = Review.objects.filter(
            product=self.product,
            verification_status='verified'
        )
        
        self.total_reviews = reviews.count()
        self.verified_reviews = reviews.filter(verification_status='verified').count()
        
        if reviews.exists():
            self.average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
            
            # Rating distribution
            self.rating_1_count = reviews.filter(rating=1).count()
            self.rating_2_count = reviews.filter(rating=2).count()
            self.rating_3_count = reviews.filter(rating=3).count()
            self.rating_4_count = reviews.filter(rating=4).count()
            self.rating_5_count = reviews.filter(rating=5).count()
            
            # Sentiment analysis
            positive = reviews.filter(sentiment_score__gte=0.6).count()
            negative = reviews.filter(sentiment_score__lte=-0.6).count()
            neutral = reviews.filter(sentiment_score__gt=-0.6, sentiment_score__lt=0.6).count()
            
            self.positive_sentiment = positive
            self.negative_sentiment = negative
            self.neutral_sentiment = neutral
            
            # Helpful votes
            self.total_helpful_votes = reviews.aggregate(
                models.Sum('helpful_count')
            )['helpful_count__sum'] or 0
            
            self.total_not_helpful_votes = reviews.aggregate(
                models.Sum('not_helpful_count')
            )['not_helpful_count__sum'] or 0
            
            total_votes = self.total_helpful_votes + self.total_not_helpful_votes
            self.helpful_ratio = self.total_helpful_votes / total_votes if total_votes > 0 else 0
        
        self.save()

class ReviewTemplate(models.Model):
    """Pre-defined review templates for products"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True)
    
    title_template = models.CharField(max_length=200, blank=True)
    content_template = models.TextField()
    
    min_rating = models.IntegerField(choices=[
        (1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), 
        (4, '4 Stars'), (5, '5 Stars')
    ], default=4)
    
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews_template'
        ordering = ['name']
    
    def __str__(self):
        return self.name