from decimal import Decimal
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    ১. সাধারণ কাস্টমার লগইন সিরিয়ালাইজার (স্টোরফ্রন্ট ও কাস্টমার ড্যাশবোর্ডের জন্য)
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = getattr(user, 'role', 'customer')
        token['tenant_id'] = user.tenant.id if getattr(user, 'tenant', None) else None
        token['subdomain'] = user.tenant.subdomain if getattr(user, 'tenant', None) else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data['user'] = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': getattr(user, 'role', 'customer'),
            'tenant': {
                'id': user.tenant.id,
                'store_name': user.tenant.store_name,
                'subdomain': user.tenant.subdomain,
            } if getattr(user, 'tenant', None) else None,
        }
        return data


class MerchantTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    ২. মার্চেন্ট পোর্টাল লগইন সিরিয়ালাইজার (কাস্টমারদের সরাসরি ব্লক করবে এবং স্টোর স্ট্যাটাস চেক করবে)
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = getattr(user, 'role', 'merchant')
        token['is_staff'] = user.is_staff
        token['subdomain'] = user.tenant.subdomain if getattr(user, 'tenant', None) else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        # কাস্টমারদের অ্যাক্সেস ব্লক
        if getattr(user, 'role', '') == 'customer' and not user.is_staff and not user.is_superuser:
            raise serializers.ValidationError({
                "detail": "এটি মার্চেন্ট অ্যাডমিন পোর্টাল। সাধারণ কাস্টমার অ্যাকাউন্ট দিয়ে এখানে প্রবেশ নিষেধ। অনুগ্রহ করে স্টোরফ্রন্ট থেকে লগইন করুন।"
            })

        # স্টোর ওনারদের ক্ষেত্রে স্টোর ও সাবস্ক্রিপশন অ্যাক্টিভেশন যাচাই
        if not user.is_superuser:
            tenant = getattr(user, 'tenant', None)
            if not tenant:
                raise serializers.ValidationError({
                    "detail": "আপনার অ্যাকাউন্টের সাথে কোনো স্টোর যুক্ত নেই। প্রথমে একটি স্টোর রেজিস্ট্রেশন করুন।"
                })

            if not tenant.is_active:
                raise serializers.ValidationError({
                    "detail": "আপনার স্টোরটি এখনও সুপার অ্যাডমিনের অনুমোদনের অপেক্ষায় রয়েছে অথবা সাবস্ক্রিপশন স্থগিত রয়েছে।"
                })

        data['user'] = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': getattr(user, 'role', 'merchant'),
            'tenant': {
                'id': user.tenant.id if user.tenant else None,
                'store_name': user.tenant.store_name if user.tenant else 'Master Platform',
                'subdomain': user.tenant.subdomain if user.tenant else 'app',
            } if getattr(user, 'tenant', None) else None,
        }
        return data


class UserSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='tenant.store_name', read_only=True)
    subdomain = serializers.CharField(source='tenant.subdomain', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'role', 'phone', 'tenant', 'store_name', 'subdomain',
            'avatar', 'bio', 'timezone',
            'email_notifications', 'push_notifications', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'role', 'tenant', 'created_at']


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "পাসওয়ার্ড দুটি মেলেনি।"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        request = self.context.get('request')
        tenant = getattr(request, 'tenant', None) if request else None

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            tenant=tenant,
            role='customer'
        )
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("বর্তমান পাসওয়ার্ডটি সঠিক নয়।")
        return value