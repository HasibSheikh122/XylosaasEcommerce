from rest_framework import serializers
from .models import StoreSettings, StoreStaff, StoreCategory, StorePage, StoreNotification


class StoreSettingsSerializer(serializers.ModelSerializer):
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)
    timezone_display = serializers.CharField(source='get_timezone_display', read_only=True)

    class Meta:
        model = StoreSettings
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class PublicStoreSettingsSerializer(serializers.ModelSerializer):
    """স্টোরফ্রন্ট ভিজিটর ও ক্রেতাদের জন্য উন্মুক্ত সেটিংস (ব্যানার, থিম, সোশ্যাল লিংক ও পলিসি)"""
    class Meta:
        model = StoreSettings
        fields = [
            'store_name', 'store_tagline', 'store_description',
            'store_logo', 'store_favicon', 'store_cover_image',
            'primary_color', 'secondary_color', 'accent_color', 'font_family',
            'contact_email', 'contact_phone', 'contact_address',
            'facebook_url', 'instagram_url', 'twitter_url', 'youtube_url', 'linkedin_url',
            'country', 'city', 'timezone', 'currency', 'currency_symbol',
            'seo_title', 'seo_description', 'seo_keywords',
            'business_hours', 'enable_guest_checkout', 'enable_cod', 'enable_online_payment',
            'privacy_policy', 'terms_conditions', 'return_policy', 'shipping_policy',
            'theme', 'theme_config', 'maintenance_mode', 'maintenance_message',
            'google_analytics_id', 'facebook_pixel_id'
        ]


class StoreStaffSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = StoreStaff
        fields = [
            'id', 'tenant', 'user', 'user_email', 'role', 'role_display',
            'permissions', 'employee_id', 'department', 'position',
            'phone', 'emergency_contact', 'emergency_contact_name',
            'hire_date', 'salary', 'status', 'work_schedule',
            'shift_start', 'shift_end', 'commission_rate', 'total_commission',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'total_commission', 'created_at', 'updated_at']


class StoreCategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)

    class Meta:
        model = StoreCategory
        fields = [
            'id', 'tenant', 'parent', 'parent_name', 'name', 'slug',
            'description', 'icon', 'image', 'display_order',
            'show_in_nav', 'show_on_homepage',
            'seo_title', 'seo_description', 'seo_keywords',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'slug', 'created_at', 'updated_at']


class StorePageSerializer(serializers.ModelSerializer):
    page_type_display = serializers.CharField(source='get_page_type_display', read_only=True)
    author_email = serializers.CharField(source='created_by.email', read_only=True)

    class Meta:
        model = StorePage
        fields = [
            'id', 'tenant', 'page_type', 'page_type_display',
            'title', 'slug', 'content', 'excerpt', 'featured_image',
            'seo_title', 'seo_description', 'seo_keywords',
            'show_in_footer', 'show_in_header', 'display_order',
            'is_published', 'is_featured', 'published_at',
            'meta_data', 'created_by', 'author_email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'slug', 'created_by', 'created_at', 'updated_at']


class StoreNotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = StoreNotification
        fields = [
            'id', 'tenant', 'notification_type', 'notification_type_display',
            'priority', 'priority_display', 'title', 'message',
            'link', 'link_text', 'show_to_all', 'is_popup', 'dismissible',
            'is_active', 'publish_from', 'publish_to', 'created_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at']