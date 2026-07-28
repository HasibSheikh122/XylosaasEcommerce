from rest_framework import serializers
from .models import Customer
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class UserRegistrationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True} # ইমেইল বাধ্যতামূলক করা
        }

    def create(self, validated_data):
        # User তৈরি করার সময় password কে সঠিকভাবে হ্যাশ করার জন্য create_user ব্যবহার করবেন
        user = User.objects.create_user(**validated_data)
        return user

class CustomerSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = (
            'user',        # ইউজার আইডি পরিবর্তনযোগ্য নয়
            'tenant',      # টেন্যান্ট পরিবর্তনযোগ্য নয়
            'total_orders', 
            'total_spent', 
            'last_order_date', 
            'customer_segment', 
            'lifetime_value', 
            'churn_risk', 
            'created_at', 
            'updated_at'
        )


