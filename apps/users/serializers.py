from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """ইউজার প্রোফাইল দেখা এবং আপডেট করার জন্য সিরিয়ালাইজার"""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'phone', 'tenant', 'avatar', 'bio', 'timezone', 
            'email_notifications', 'push_notifications', 'created_at'
        ]
        read_only_fields = ['id', 'role', 'tenant', 'created_at']


class UserRegisterSerializer(serializers.ModelSerializer):
    """নতুন ইউজার/কাস্টমার রেজিস্ট্রেশনের জন্য সিরিয়ালাইজার"""
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'phone']

    def create(self, validated_data):
        # জ্যাঙ্গো স্টাইল অনুযায়ী পাসওয়ার্ড হ্যাশ করে ইউজার তৈরি করা
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            role='customer'  # ডিফল্টভাবে সবাই কাস্টমার হিসেবে রেজিস্টার্ড হবে
        )
        return user