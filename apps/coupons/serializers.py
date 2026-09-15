from decimal import Decimal
from rest_framework import serializers
from .models import Coupon, CouponUsage, CouponRule, CouponCategory


class CouponCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponCategory
        fields = ['id', 'tenant', 'name', 'description', 'color', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class CouponRuleSerializer(serializers.ModelSerializer):
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)

    class Meta:
        model = CouponRule
        fields = ['id', 'coupon', 'rule_type', 'rule_type_display', 'rule_value', 'is_required', 'order', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CouponSerializer(serializers.ModelSerializer):
    discount_type_display = serializers.CharField(source='get_discount_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    rules = CouponRuleSerializer(many=True, read_only=True)

    class Meta:
        model = Coupon
        fields = [
            'id', 'tenant', 'code', 'name', 'description',
            'discount_type', 'discount_type_display', 'discount_value', 'max_discount_amount',
            'buy_quantity', 'get_quantity', 'get_discount_percentage',
            'apply_to', 'applicable_categories', 'applicable_products', 'excluded_products',
            'usage_limit', 'per_user_limit', 'used_count',
            'valid_from', 'valid_to',
            'minimum_order_amount', 'maximum_order_amount',
            'new_customers_only', 'first_order_only', 'applicable_customer_segments',
            'status', 'status_display', 'show_on_checkout', 'is_public',
            'can_combine', 'priority', 'rules', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'used_count', 'created_by', 'created_at', 'updated_at']

    def validate(self, attrs):
        # ভ্যালিডেশনের সময় তারিখ যাচাই
        valid_from = attrs.get('valid_from', getattr(self.instance, 'valid_from', None))
        valid_to = attrs.get('valid_to', getattr(self.instance, 'valid_to', None))
        if valid_from and valid_to and valid_from >= valid_to:
            raise serializers.ValidationError({"valid_to": "কুপনের শেষ তারিখ অবশ্যই শুরুর তারিখের পরবর্তী হতে হবে।"})
        return attrs


class CouponUsageSerializer(serializers.ModelSerializer):
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model = CouponUsage
        fields = [
            'id', 'coupon', 'coupon_code', 'order', 'order_number', 'customer',
            'discount_amount', 'original_amount', 'final_amount',
            'is_valid', 'is_refunded', 'ip_address', 'user_agent', 'used_at'
        ]
        read_only_fields = ['id', 'used_at']


class ValidateCouponRequestSerializer(serializers.Serializer):
    """চেকআউটে ফ্রন্টএন্ড থেকে কুপন কোড টেস্ট করার ইনপুট ভ্যালিডেশন"""
    code = serializers.CharField(max_length=50)
    cart_total = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.00'))
    customer_id = serializers.IntegerField(required=False, allow_null=True)