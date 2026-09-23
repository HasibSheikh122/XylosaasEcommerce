# apps/stores/serializers.py
from rest_framework import serializers
from .models import (
    StoreSettings,
    StoreCategory,
    StoreBanner,
    StoreFAQ,
    StoreTestimonial,
    StoreNewsletterSubscriber,
    StoreBlogPost,
    StoreGalleryImage
)

class StoreSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreSettings
        fields = [
            'store_name', 'store_tagline', 'store_description',
            'store_logo', 'store_favicon', 'store_cover_image',
            'show_announcement_bar', 'announcement_text', 'announcement_phone',
            'primary_color', 'secondary_color', 'accent_color', 'font_family',
            'contact_email', 'contact_phone', 'contact_address',
            'facebook_url', 'instagram_url', 'twitter_url',
            'currency', 'currency_symbol', 'subdomain',
            'theme', 'theme_config', 'enable_cod', 'enable_online_payment',
        ]


class StoreCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'image', 'display_order', 'show_on_homepage',
        ]


class StoreBannerSerializer(serializers.ModelSerializer):
    banner_type_display = serializers.CharField(source='get_banner_type_display', read_only=True)
    is_active = serializers.BooleanField(default=True)

    class Meta:
        model = StoreBanner
        fields = [
            'id',
            'tenant',
            'banner_type',
            'banner_type_display',
            'badge_title',
            'title',
            'subtitle',
            'image',
            'secondary_image',
            'button_text',
            'target_url',
            'countdown_end',
            'display_order',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']

    def validate_countdown_end(self, value):
        if value == "" or value is None:
            return None
        return value


class StoreFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreFAQ
        fields = ['id', 'question', 'answer', 'display_order']


# 🌟 মার্চেন্ট ও স্টোরফ্রন্টের জন্য টেস্টমোনিয়াল সিরিয়ালাইজার
class StoreTestimonialSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = StoreTestimonial
        fields = [
            'id',
            'tenant',
            'customer_name',
            'designation',
            'avatar',
            'avatar_url',
            'rating',
            'comment',
            'is_featured',
            'display_order',
            'created_at',
        ]
        read_only_fields = ['id', 'tenant', 'created_at']

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            url = obj.avatar.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None



class StoreNewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreNewsletterSubscriber
        fields = ['email']


# 🌟 News & Blogs Serializer
class StoreBlogPostSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = StoreBlogPost
        fields = [
            'id',
            'tenant',
            'title',
            'slug',
            'category_tag',
            'author_name',
            'cover_image',
            'cover_image_url',
            'summary',
            'content',
            'published_at',
            'is_published',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'tenant', 'slug', 'published_at', 'created_at', 'updated_at']

    def get_cover_image_url(self, obj):
        request = self.context.get('request')
        if obj.cover_image:
            url = obj.cover_image.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

# apps/stores/serializers.py এর নিচে যোগ করুন:
# apps/stores/serializers.py ফাইলের নিচের অংশটি আপডেট করুন:

class StoreNewsletterSubscriberSerializer(serializers.ModelSerializer):
    """মার্চেন্ট ড্যাশবোর্ডে গ্রাহকদের সাবস্ক্রাইব করা ইমেইল লিস্ট দেখানোর জন্য"""
    created_at = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = StoreNewsletterSubscriber
        fields = ['id', 'email', 'created_at']

    def get_created_at(self, obj):
        # মডেলে যে ফিল্ডই থাকুক (created_at, subscribed_at বা created) তা খুঁজে রিটার্ন করবে
        for attr in ['created_at', 'subscribed_at', 'created', 'created_on', 'timestamp']:
            val = getattr(obj, attr, None)
            if val:
                return val
        return None




class StoreGalleryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreGalleryImage
        fields = ['id', 'image']