from rest_framework import serializers
from .models import Review, ReviewReply, ReviewReport, ReviewPhoto, ReviewAnalytics, ReviewTemplate


class ReviewPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewPhoto
        fields = ['id', 'review', 'media_file', 'media_type', 'alt_text', 'is_primary', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReviewReplySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = ReviewReply
        fields = ['id', 'review', 'user', 'user_name', 'content', 'is_owner_reply', 'attachments', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ReviewSerializer(serializers.ModelSerializer):
    replies = ReviewReplySerializer(many=True, read_only=True)
    review_photos = ReviewPhotoSerializer(many=True, read_only=True)
    customer_display_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'tenant', 'product', 'customer', 'customer_display_name', 'order',
            'title', 'content', 'rating', 'images', 'videos',
            'verification_status', 'verified_purchase',
            'helpful_count', 'not_helpful_count', 'is_featured', 'is_anonymous',
            'replies', 'review_photos', 'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = [
            'id', 'tenant', 'customer', 'verification_status', 'verified_purchase',
            'helpful_count', 'not_helpful_count', 'sentiment_score', 'moderation_status',
            'created_at', 'updated_at'
        ]

    def get_customer_display_name(self, obj):
        if obj.is_anonymous:
            return "Anonymous Customer"
        if obj.customer:
            return getattr(obj.customer, 'name', 'Verified Customer')
        return "Customer"


class ReviewReportSerializer(serializers.ModelSerializer):
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)

    class Meta:
        model = ReviewReport
        fields = ['id', 'review', 'reported_by', 'reason', 'reason_display', 'description', 'status', 'created_at']
        read_only_fields = ['id', 'reported_by', 'status', 'created_at']


class ReviewAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewAnalytics
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'product', 'last_updated']


class ReviewTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewTemplate
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']