from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Plan, Subscription

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_details = PlanSerializer(source='plan', read_only=True)
    tenant_name = serializers.CharField(source='tenant.store_name', read_only=True)

    class Meta:
        model = Subscription
        fields = '__all__'
        read_only_fields = (
            'status', 'trial_start', 'trial_end', 
            'current_period_start', 'current_period_end', 
            'canceled_at', 'created_at', 'updated_at'
        )

    def validate(self, attrs):
        # একটি টেন্যান্টের অলরেডি একটি অ্যাক্টিভ সাবস্ক্রিপশন থাকলে নতুন করে তৈরি করতে দেবে না
        tenant = attrs.get('tenant')
        if Subscription.objects.filter(tenant=tenant, status__in=['active', 'trial']).exists():
            raise serializers.ValidationError("This tenant already has an active subscription or trial.")
        return attrs

    def create(self, validated_data):
        # ➔ বিজনেস লজিক: নতুন সাবস্ক্রিপশন নিলে অটোমেটিক ১৪ দিনের ট্রায়াল পিরিয়ড সেট হবে
        now = timezone.now()
        validated_data['trial_start'] = now
        validated_data['trial_end'] = now + timedelta(days=14)
        validated_data['current_period_start'] = now
        validated_data['current_period_end'] = now + timedelta(days=14) # ট্রায়াল শেষে বিলিং শুরু হবে
        validated_data['status'] = 'trial'
        
        return super().create(validated_data)