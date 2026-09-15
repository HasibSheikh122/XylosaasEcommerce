from rest_framework import serializers
from .models import (
    AIRecommendation,
    ChatbotInteraction,
    DemandForecast,
    DynamicPrice,
    CustomerSegment,
    FraudDetection,
    AIContent,
)


class AIRecommendationSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)

    class Meta:
        model = AIRecommendation
        fields = [
            'id', 'tenant', 'customer', 'customer_email', 'product', 'product_name',
            'score', 'reason', 'viewed', 'clicked', 'purchased', 'created_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at']


class ChatbotInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatbotInteraction
        fields = [
            'id', 'tenant', 'customer', 'session_id',
            'question', 'response', 'intent', 'confidence',
            'was_helpful', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at']


class DemandForecastSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = DemandForecast
        fields = [
            'id', 'tenant', 'product', 'product_name', 'forecast_date',
            'predicted_quantity', 'confidence_lower', 'confidence_upper',
            'actual_quantity', 'model_used', 'accuracy_score', 'created_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at']


class DynamicPriceSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = DynamicPrice
        fields = [
            'id', 'tenant', 'product', 'product_name', 'base_price', 'current_price',
            'predicted_price', 'demand_score', 'competitor_price', 'inventory_level',
            'strategy_used', 'update_reason', 'created_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at']


class CustomerSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerSegment
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class FraudDetectionSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    reviewed_by_email = serializers.CharField(source='reviewed_by.email', read_only=True)

    class Meta:
        model = FraudDetection
        fields = [
            'id', 'tenant', 'order', 'order_number', 'risk_score', 'risk_level',
            'factors', 'recommendations', 'is_flagged', 'is_reviewed',
            'reviewed_by', 'reviewed_by_email', 'created_at'
        ]
        read_only_fields = ['id', 'tenant', 'reviewed_by', 'created_at']


class AIContentSerializer(serializers.ModelSerializer):
    content_type_display = serializers.CharField(source='get_content_type_display', read_only=True)
    approved_by_email = serializers.CharField(source='approved_by.email', read_only=True)

    class Meta:
        model = AIContent
        fields = [
            'id', 'tenant', 'content_type', 'content_type_display',
            'source_data', 'generated_content', 'ai_metadata',
            'is_approved', 'approved_by', 'approved_by_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'approved_by', 'created_at', 'updated_at']