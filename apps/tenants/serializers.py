import re
from datetime import timedelta
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction

from apps.tenants.models import Tenant, Domain
from apps.subscriptions.models import Plan


class TenantRegistrationSerializer(serializers.ModelSerializer):
    plan = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.filter(is_active=True),
        required=True,
        error_messages={'does_not_exist': 'The selected subscription plan is inactive or invalid.'}
    )

    class Meta:
        model = Tenant
        fields = ['store_name', 'subdomain', 'plan']

    def validate(self, attrs):
        request = self.context.get('request')
        
        if request and request.user.is_authenticated:
            user = request.user
            # নিরাপদ টেন্যান্ট ওনারশিপ চেক
            user_tenant = getattr(user, 'tenant', None)
            if user_tenant and user_tenant.is_active:
                raise serializers.ValidationError(
                    {"user": "You already have an active store. Your account is limited to one store at a time."}
                )
                
        return attrs

    def validate_store_name(self, value):
        value = " ".join(value.split())
        if len(value) < 3 or len(value) > 100:
            raise serializers.ValidationError("Store name must be between 3 and 100 characters long.")
            
        if not re.match(r'^[a-zA-Z0-9\s\-\.\,\&\']+$', value):
            raise serializers.ValidationError("Store name contains unsupported special characters.")
            
        return value

    def validate_subdomain(self, value):
        value = value.lower().strip()

        reserved_keywords = {
            'admin', 'administrator', 'api', 'root', 'www', 'mail', 'secure',
            'shophive', 'xyloshop', 'xylosaas', 'support', 'billing', 'dashboard',
            'static', 'media', 'assets', 'blog', 'dev', 'test', 'status', 'auth',
            'login', 'register', 'signup', 'logout', 'user', 'users', 'tenant', 'tenants',
            'config', 'settings', 'payment', 'checkout', 'cart', 'order', 'orders', 'help'
        }
        if value in reserved_keywords:
            raise serializers.ValidationError(f"'{value}' is reserved for platform infrastructure and cannot be used.")

        if not re.match(r'^[a-z0-9](-?[a-z0-9])*$', value):
            raise serializers.ValidationError(
                "Subdomain must contain only lowercase alphanumeric characters or hyphens, and cannot start/end with a hyphen."
            )

        if len(value) < 3 or len(value) > 63:
            raise serializers.ValidationError("Subdomain must be between 3 and 63 characters.")

        if Tenant.objects.filter(subdomain=value).exists():
            raise serializers.ValidationError("This subdomain is already registered by another merchant.")

        return value

    def create(self, validated_data):
        subdomain = validated_data['subdomain']
        validated_data['schema_name'] = subdomain 
        # Database NOT NULL কনস্ট্রেইন্ট ফিক্স:
        validated_data['name'] = validated_data.get('name') or validated_data['store_name']
        plan = validated_data['plan']
        
        # ট্রায়াল এবং সাবস্ক্রিপশন মেয়াদ ক্যালকুলেশন
        now = timezone.now()
        trial_days = getattr(plan, 'trial_days', 0)
        if trial_days > 0:
            validated_data['is_trial'] = True
            validated_data['trial_ends_at'] = now + timedelta(days=trial_days)
            validated_data['subscription_end_date'] = validated_data['trial_ends_at']
        else:
            validated_data['is_trial'] = False
            validated_data['subscription_end_date'] = now + timedelta(days=30)

        # রিসোর্স কোটা অ্যাসাইনমেন্ট
        validated_data['max_products'] = getattr(plan, 'max_products', 100)
        validated_data['max_staff'] = getattr(plan, 'max_staff', 5)
        validated_data['max_orders_per_month'] = getattr(plan, 'max_orders', 500)
        validated_data['ai_enabled'] = getattr(plan, 'ai_features_allowed', False)

        request = self.context.get('request')

        with transaction.atomic():
            tenant = super().create(validated_data)
            
            # লোকাল এবং সাবডোমেন রাউটিং
            full_domain = f"{subdomain}.localhost"
            Domain.objects.create(
                domain=full_domain,
                tenant=tenant,
                is_primary=True
            )

            if request and request.user.is_authenticated:
                user = request.user
                user.tenant = tenant
                user.role = 'store_owner' 
                user.save()

        return tenant


class MerchantStoreDetailSerializer(serializers.ModelSerializer):
    """স্টোরের সেটিংস দেখা এবং ওনার কর্তৃক আপডেট করার সিরিয়ালাইজার"""
    assigned_domain = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            'id',
            'store_name',
            'subdomain',
            'schema_name',
            'assigned_domain',
            'custom_domain',
            'logo',
            'favicon',
            'is_active',
            'max_products',
            'max_staff',
            'max_orders_per_month',
            'ai_enabled',
            'is_trial',
            'trial_ends_at',
            'subscription_end_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'subdomain',
            'schema_name',
            'assigned_domain',
            'is_active',
            'max_products',
            'max_staff',
            'max_orders_per_month',
            'ai_enabled',
            'is_trial',
            'trial_ends_at',
            'subscription_end_date',
            'created_at',
            'updated_at',
        ]

    def get_assigned_domain(self, obj):
        primary = obj.domains.filter(is_primary=True).first()
        return primary.domain if primary else f"{obj.subdomain}.localhost"