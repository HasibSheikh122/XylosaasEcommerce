# apps/customers/serializers.py
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from rest_framework import serializers
from .models import Customer
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserRegistrationSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name', 'phone')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def create(self, validated_data):
        validated_data.pop('phone', None)
        user = User.objects.create_user(**validated_data)
        return user


class CustomerSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    last_active = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'id', 'tenant', 'user', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'total_orders', 'total_spent', 'last_order_date',
            'last_active', 'is_online', 'customer_segment', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_is_online(self, obj):
        # Shudhu matro live heartbeat cache thaklei True hobe
        clean_email = obj.email.strip().lower() if obj.email else ''
        if clean_email and cache.get(f"online_customer_{clean_email}"):
            return True
        return False

    def get_last_active(self, obj):
        clean_email = obj.email.strip().lower() if obj.email else ''
        cached_time = cache.get(f"online_customer_{clean_email}")
        if cached_time:
            return cached_time

        # Shudhu real user activities (login ba order date) count hobe
        if obj.user and obj.user.last_login:
            return obj.user.last_login
        if obj.last_order_date:
            return obj.last_order_date
        return obj.created_at