import re
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from apps.tenants.models import Tenant, Domain
from apps.subscriptions.models import Plan

class TenantRegistrationSerializer(serializers.ModelSerializer):
    # শুধু একটি আইডি নিলেই হবে না, প্ল্যানটি যেন অ্যাক্টিভ থাকে তাও ব্যাকএন্ডে চেক করবে
    plan = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.filter(is_active=True),
        required=True,
        error_messages={'does_not_exist': 'The selected subscription plan is inactive or invalid.'}
    )

    class Meta:
        model = Tenant
        fields = ['store_name', 'subdomain', 'plan']

    def validate(self, attrs):
        """ 
        মাল্টি-ফিল্ড ক্রস ভ্যালিডেশন: 
        এখানে এমন লজিক থাকবে যা একাধিক ফিল্ড এবং রিকোয়েস্ট ইউজারের ওপর নির্ভর করে।
        """
        request = self.context.get('request')
        
        if request and request.user.is_authenticated:
            user = request.user
            
            # 🔒 অ্যান্টি-অ্যাবিউজ লজিক: চেক করা ইউজার অলরেডি কোনো একটিভ টেন্যান্টের ওনার কিনা
            # (SaaS বিজনেসে সাধারণত ফ্রিতে বা একটি অ্যাকাউন্টে একাধিক শপ খুলতে দেওয়া হয় না, যদি না প্রিমিয়াম প্ল্যান থাকে)
            has_active_tenant = Tenant.objects.filter(
                subdomain=user.tenant.subdomain if user.tenant else None, 
                is_active=True
            ).exists()
            
            if has_active_tenant:
                raise serializers.ValidationError(
                    {"user": "You already have an active store. Your account is limited to one store at a time."}
                )
                
        return attrs

    def validate_store_name(self, value):
        # একাধিক স্পেস থাকলে তা সিঙ্গেল স্পেসে রূপান্তর করা (যেমন: "My   Super   Shop" -> "My Super Shop")
        value = " ".join(value.split())
        
        if len(value) < 3 or len(value) > 100:
            raise serializers.ValidationError("Store name must be between 3 and 100 characters long.")
            
        # ক্যারেক্টার ভ্যালিডেশন (নিরাপদ নাম নিশ্চিত করা)
        if not re.match(r'^[a-zA-Z0-9\s\-\.\,\&\']+$', value):
            raise serializers.ValidationError("Store name contains unsupported special characters.")
            
        return value

    def validate_subdomain(self, value):
        value = value.lower().strip()

        # ১. ব্লকলিস্টেড বা সিস্টেম ডোমেন প্রোটেকশন
        reserved_keywords = {
            'admin', 'administrator', 'api', 'root', 'www', 'mail', 'secure',
            'shophive', 'xyloshop', 'xylosaas', 'support', 'billing', 'dashboard',
            'static', 'media', 'assets', 'blog', 'dev', 'test', 'status', 'auth',
            'login', 'register', 'signup', 'logout', 'user', 'users', 'tenant', 'tenants',
            'config', 'settings', 'payment', 'checkout', 'cart', 'order', 'orders', 'help'
        }
        if value in reserved_keywords:
            raise serializers.ValidationError(f"'{value}' is reserved for platform infrastructure and cannot be used.")

        # ২. ডোমেন নেম স্ট্যান্ডার্ড (কোনো হাইফেন দিয়ে শুরু বা শেষ হতে পারবে না, আন্ডারস্কোর নিষিদ্ধ)
        if not re.match(r'^[a-z0-9](-?[a-z0-9])*$', value):
            raise serializers.ValidationError(
                "Subdomain must contain only lowercase alphanumeric characters or hyphens, and cannot start/end with a hyphen."
            )

        if len(value) < 3 or len(value) > 63:
            raise serializers.ValidationError("Subdomain must be between 3 and 63 characters.")

        # ৩. ডুপ্লিকেট চেক
        if Tenant.objects.filter(subdomain=value).exists():
            raise serializers.ValidationError("This subdomain is already registered by another merchant.")

        return value

    def create(self, validated_data):
        """ 
        অ্যাটোমিক ট্রানজেকশন এবং ডাইনামিক কোটা পলিসি 
        """
        subdomain = validated_data['subdomain']
        validated_data['schema_name'] = subdomain 
        plan = validated_data['plan']
        
        # টাইম ক্যালকুলেশন
        now = timezone.now()
        if getattr(plan, 'trial_days', 0) > 0:
            validated_data['is_trial'] = True
            validated_data['trial_ends_at'] = now + timedelta(days=plan.trial_days)
            validated_data['subscription_end_date'] = validated_data['trial_ends_at']
        else:
            validated_data['is_trial'] = False
            validated_data['subscription_end_date'] = now + timedelta(days=30)

        # রিসোর্স লিমিট এসাইনমেন্ট
        validated_data['max_products'] = getattr(plan, 'max_products', 100)
        validated_data['max_staff'] = getattr(plan, 'max_staff', 5)
        validated_data['max_orders_per_month'] = getattr(plan, 'max_orders', 500)
        validated_data['ai_enabled'] = getattr(plan, 'ai_features_allowed', False)

        request = self.context.get('request')

        # 🔥 ডাটাবেস ট্রানজেকশন লক: স্কিমা বা ডোমেন যেকোনো একটি ফেইল করলে যেন কোনো ডেটা ক্রাশ না করে
        with transaction.atomic():
            # ১. টেন্যান্ট এবং পোস্টগ্রেস স্কিমা তৈরি (django-tenants ব্যাকএন্ড ট্র্রিগার করবে)
            tenant = super().create(validated_data)
            
            # ২. এই টেন্যান্টের জন্য সাথে সাথে ডোমেন ম্যাপ ক্রিয়েট করা (লোকালহোস্ট ও প্রোডাকশন হ্যান্ডেল করবে)
            # প্রোডাকশনে এটি আপনার মেইন ডোমেন (যেমন: shophive.ai) এর সাথে যুক্ত হবে
            full_domain = f"{subdomain}.localhost" # অথবা সেটিংস থেকে ডাইনামিক ডোমেন নিতে পারেন
            Domain.objects.create(
                domain=full_domain,
                tenant=tenant,
                is_primary=True
            )

            # ৩. ওনারশিপ ম্যাপিং ও রোল পরিবর্তন
            if request and request.user.is_authenticated:
                user = request.user
                user.tenant = tenant
                user.role = 'store_owner' 
                user.save()

        return tenant