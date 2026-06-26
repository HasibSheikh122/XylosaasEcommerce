from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline
from .models import Review, ReviewReply, ReviewReport, ReviewPhoto, ReviewAnalytics, ReviewTemplate

class ReviewPhotoInline(TabularInline):
    model = ReviewPhoto
    extra = 0
    fields = ('media_file', 'media_type', 'is_primary', 'order')

class ReviewReplyInline(TabularInline):
    model = ReviewReply
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ('product', 'customer', 'rating', 'verification_status', 'is_featured', 'created_at')
    list_filter = ('verification_status', 'rating', 'is_featured', 'tenant')
    search_fields = ('product__name', 'customer__email', 'content')
    inlines = [ReviewPhotoInline, ReviewReplyInline]
    
    fieldsets = (
        ('Basic Information', {'fields': ('tenant', 'product', 'customer', 'order', 'title', 'content', 'rating')}),
        ('Moderation & Status', {'fields': ('verification_status', 'verification_date', 'verified_by', 'verified_purchase', 'moderation_status', 'flagged_count')}),
        ('Metrics & AI', {'fields': ('helpful_count', 'not_helpful_count', 'sentiment_score', 'is_featured', 'is_anonymous')}),
        ('SEO & Metadata', {'fields': ('seo_meta_title', 'seo_meta_description', 'ip_address'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ReviewAnalytics)
class ReviewAnalyticsAdmin(ModelAdmin):
    list_display = ('product', 'total_reviews', 'average_rating', 'helpful_ratio')
    list_filter = ('tenant',)
    readonly_fields = ('total_reviews', 'verified_reviews', 'average_rating', 'helpful_ratio', 'last_updated')

@admin.register(ReviewReport)
class ReviewReportAdmin(ModelAdmin):
    list_display = ('review', 'reported_by', 'reason', 'status')
    list_filter = ('status', 'reason')
    readonly_fields = ('created_at',)

@admin.register(ReviewTemplate)
class ReviewTemplateAdmin(ModelAdmin):
    list_display = ('name', 'tenant', 'min_rating', 'is_active')
    list_filter = ('tenant', 'is_active')

@admin.register(ReviewReply)
class ReviewReplyAdmin(ModelAdmin):
    list_display = ('review', 'user', 'is_owner_reply', 'is_approved')
    list_filter = ('is_approved', 'is_owner_reply')

@admin.register(ReviewPhoto)
class ReviewPhotoAdmin(ModelAdmin):
    list_display = ('review', 'media_type', 'is_primary', 'is_approved')