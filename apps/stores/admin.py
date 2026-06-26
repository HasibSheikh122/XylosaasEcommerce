from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import StoreSettings, StoreStaff, StoreCategory, StorePage, StoreNotification

@admin.register(StoreSettings)
class StoreSettingsAdmin(ModelAdmin):
    list_display = ('store_name', 'tenant', 'currency', 'theme')
    list_filter = ('currency', 'tenant')
    fieldsets = (
        ('General Info', {'fields': ('tenant', 'store_name', 'store_tagline', 'store_description', 'store_logo', 'store_favicon')}),
        ('Branding & Theme', {'fields': ('primary_color', 'secondary_color', 'accent_color', 'font_family', 'theme', 'custom_css', 'custom_js'), 'classes': ('collapse',)}),
        ('Regional & Domain', {'fields': ('country', 'city', 'timezone', 'currency', 'currency_symbol', 'subdomain', 'custom_domain')}),
        ('Policies & Checkout', {'fields': ('enable_guest_checkout', 'enable_cod', 'enable_online_payment', 'privacy_policy', 'terms_conditions', 'return_policy', 'shipping_policy'), 'classes': ('collapse',)}),
        ('Tracking & SEO', {'fields': ('google_analytics_id', 'facebook_pixel_id', 'seo_title', 'seo_description', 'seo_keywords')}),
    )

@admin.register(StoreStaff)
class StoreStaffAdmin(ModelAdmin):
    list_display = ('user', 'tenant', 'role', 'status', 'position')
    list_filter = ('role', 'status', 'tenant')
    search_fields = ('user__email', 'employee_id')

@admin.register(StoreCategory)
class StoreCategoryAdmin(ModelAdmin):
    list_display = ('name', 'tenant', 'is_active', 'display_order', 'show_in_nav')
    list_filter = ('is_active', 'tenant')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(StorePage)
class StorePageAdmin(ModelAdmin):
    list_display = ('title', 'page_type', 'is_published', 'show_in_header', 'show_in_footer')
    list_filter = ('page_type', 'is_published', 'tenant')
    prepopulated_fields = {'slug': ('title',)} # স্লাগ জেনারেট করার জন্য টাইটেল ব্যবহার করুন
    fieldsets = (
        ('Page Content', {'fields': ('tenant', 'page_type', 'title', 'slug', 'content', 'excerpt')}),
        ('Display & SEO', {'fields': ('show_in_header', 'show_in_footer', 'display_order', 'is_published', 'seo_title', 'seo_description')}),
    )

@admin.register(StoreNotification)
class StoreNotificationAdmin(ModelAdmin):
    list_display = ('title', 'notification_type', 'priority', 'publish_from', 'is_active')
    list_filter = ('notification_type', 'priority', 'is_active')