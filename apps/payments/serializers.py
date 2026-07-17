from rest_framework import serializers
from .models import (
    PaymentGateway, PaymentTransaction, 
    PaymentSubscription, PaymentRefund, PaymentLog
)

class PaymentGatewaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentGateway
        fields = '__all__'
        # API Keys গুলো সাধারণত response-এ দেখানো উচিত নয়
        extra_kwargs = {
            'api_key': {'write_only': True},
            'api_secret': {'write_only': True},
            'api_password': {'write_only': True},
        }

class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = '__all__'
        read_only_fields = ['transaction_id', 'status', 'initiated_at']

class PaymentSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentSubscription
        fields = '__all__'

class PaymentRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRefund
        fields = '__all__'
        read_only_fields = ['status', 'processed_at']

class PaymentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLog
        fields = '__all__'