from django.contrib import admin
from django.db import connection
from django.utils.html import format_html
from .models import (
    StoreSettings,
    StoreBanner,
    StoreCategory,
    StoreFAQ,
    StoreTestimonial,
    StoreNewsletterSubscriber,
    StoreBlogPost,
    StoreStaff,
    StorePage,
    StoreNotification,
)


class BaseTenantAdmin(admin.ModelAdmin):
    """স্বয়ংক্রিয়ভাবে কারেন্ট টেন্যান্ট অ্যাসাইন করার জন্য বেস অ্যাডমিন"""
    def save_model(self, request, obj, form, change):
        if not getattr(obj, 'tenant_id', None):
            tenant = getattr(request, 'tenant', None) or getattr(connection, 'tenant', None)
            if tenant:
                obj.tenant = tenant
        super().save_model(request, obj, form, change)


@admin.register(StoreBanner)
class StoreBannerAdmin(BaseTenantAdmin):
    list_display = (
        'title',
        'banner_type',
        'left_preview',
        'right_preview',
        'countdown_end',
        'display_order',
        'is_active',
    )
    list_filter = ('banner_type', 'is_active')
    search_fields = ('title', 'subtitle', 'badge_title')
    list_editable = ('display_order', 'is_active')

    fieldsets = (
        ('Banner Classification', {
            'fields': ('banner_type', 'badge_title', 'title', 'subtitle')
        }),
        ('Images (Left & Right)', {
            'fields': ('image', 'secondary_image'),
            'description': 'Summer Countdown ব্যানারের ক্ষেত্রে: image = বাম পাশের ছবি, secondary_image = ডান পাশের ছবি।'
        }),
        ('Call To Action', {
            'fields': ('button_text', 'target_url')
        }),
        ('Timer Settings', {
            'fields': ('countdown_end',),
            'description': 'অফারটি শেষ হওয়ার সুনির্দিষ্ট তারিখ ও সময় নির্ধারণ করুন।'
        }),
        ('Display Controls', {
            'fields': ('display_order', 'is_active')
        }),
    )

    def left_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 35px; object-fit: cover; border-radius: 6px;" />',
                obj.image.url
            )
        return "-"
    left_preview.short_description = "Left Image"

    def right_preview(self, obj):
        if obj.secondary_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 35px; object-fit: cover; border-radius: 6px;" />',
                obj.secondary_image.url
            )
        return "-"
    right_preview.short_description = "Right Image"


@admin.register(StoreSettings)
class StoreSettingsAdmin(BaseTenantAdmin):
    list_display = ('store_name', 'subdomain', 'currency', 'theme', 'show_announcement_bar')


@admin.register(StoreCategory)
class StoreCategoryAdmin(BaseTenantAdmin):
    list_display = ('name', 'slug', 'display_order', 'show_on_homepage', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('display_order', 'show_on_homepage', 'is_active')


@admin.register(StoreFAQ)
class StoreFAQAdmin(BaseTenantAdmin):
    list_display = ('question', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')


@admin.register(StoreTestimonial)
class StoreTestimonialAdmin(BaseTenantAdmin):
    list_display = ('customer_name', 'designation', 'rating', 'is_featured')
    list_filter = ('rating', 'is_featured')


@admin.register(StoreBlogPost)
class StoreBlogPostAdmin(BaseTenantAdmin):
    list_display = ('title', 'category_tag', 'author_name', 'published_at', 'is_published')
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ('is_published', 'category_tag')


@admin.register(StoreNewsletterSubscriber)
class StoreNewsletterSubscriberAdmin(BaseTenantAdmin):
    list_display = ('email', 'subscribed_at')
    search_fields = ('email',)


@admin.register(StoreStaff)
class StoreStaffAdmin(BaseTenantAdmin):
    list_display = ('user', 'role', 'department', 'status')
    list_filter = ('role', 'status')


@admin.register(StorePage)
class StorePageAdmin(BaseTenantAdmin):
    list_display = ('title', 'page_type', 'is_published', 'show_in_footer')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(StoreNotification)
class StoreNotificationAdmin(BaseTenantAdmin):
    list_display = ('title', 'notification_type', 'priority', 'is_active')