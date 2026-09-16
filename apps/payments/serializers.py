from rest_framework import serializers
from .models import (
    PaymentGateway,
    PaymentTransaction,
    PaymentSubscription,
    PaymentRefund,
    PaymentLog,
)


class PaymentGatewaySerializer(serializers.ModelSerializer):
    gateway_type_display = serializers.CharField(source='get_gateway_type_display', read_only=True)

    class Meta:
        model = PaymentGateway
        fields = [
            'id', 'tenant', 'gateway_type', 'gateway_type_display',
            'is_active', 'is_default',
            'api_key', 'api_secret', 'api_username', 'api_password',
            'gateway_settings', 'transaction_fee_percentage', 'transaction_fee_fixed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']
        extra_kwargs = {
            'api_secret': {'write_only': True},
            'api_password': {'write_only': True},
        }


class PaymentTransactionSerializer(serializers.ModelSerializer):
    gateway_name = serializers.CharField(source='gateway.get_gateway_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'tenant', 'order', 'customer', 'gateway', 'gateway_name',
            'transaction_id', 'order_number', 'invoice_number',
            'amount', 'currency', 'tax_amount', 'fee_amount', 'discount_amount', 'net_amount',
            'payment_method', 'status', 'status_display',
            'gateway_transaction_id', 'gateway_response', 'gateway_error',
            'customer_name', 'customer_email', 'customer_phone', 'billing_address',
            'card_last_four', 'card_brand', 'card_expiry',
            'refund_status', 'refund_amount', 'refund_transaction_id', 'refund_reason',
            'initiated_at', 'completed_at', 'failed_at', 'refunded_at',
            'metadata', 'notes'
        ]
        read_only_fields = [
            'id', 'tenant', 'transaction_id', 'status',
            'initiated_at', 'completed_at', 'failed_at', 'refunded_at'
        ]


class InitiatePaymentSerializer(serializers.Serializer):
    """চেকআউট অর্ডারের বিপরীতে পেমেন্ট গেটওয়ে শুরু করার ইনপুট ভ্যালিডেশন"""
    order_id = serializers.IntegerField(required=True)
    gateway_type = serializers.ChoiceField(choices=PaymentGateway.GATEWAY_TYPES, required=True)
    payment_method = serializers.ChoiceField(choices=PaymentTransaction.PAYMENT_METHODS, default='mobile_banking')


class PaymentRefundSerializer(serializers.ModelSerializer):
    reason_display = serializers.CharField(source='get_refund_reason_display', read_only=True)
    approved_by_email = serializers.CharField(source='approved_by.email', read_only=True)

    class Meta:
        model = PaymentRefund
        fields = [
            'id', 'tenant', 'transaction', 'refund_transaction_id',
            'refund_amount', 'refund_reason', 'reason_display', 'refund_reason_detail',
            'gateway_response', 'is_approved', 'approved_by', 'approved_by_email',
            'status', 'notes', 'created_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'tenant', 'refund_transaction_id', 'is_approved',
            'approved_by', 'status', 'created_at', 'processed_at'
        ]


class PaymentSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentSubscription
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'payment_date']


class PaymentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLog
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at']