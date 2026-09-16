from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    লগইন করার পর JWT টোকেনের পাশাপাশি ইউজারের রোল, টেন্যান্ট এবং প্রোফাইল তথ্য রেসপন্সে পাঠাবে
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # JWT Payload-এ কাস্টম ক্লেইমস
        token['email'] = user.email
        token['role'] = user.role
        token['tenant_id'] = user.tenant.id if user.tenant else None
        token['subdomain'] = user.tenant.subdomain if user.tenant else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # লগইন রেসপন্স বডিতে অতিরিক্ত তথ্য যুক্ত করা
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'tenant': {
                'id': self.user.tenant.id,
                'store_name': self.user.tenant.store_name,
                'subdomain': self.user.tenant.subdomain,
            } if self.user.tenant else None,
        }
        return data


class UserSerializer(serializers.ModelSerializer):
    """ইউজার প্রোফাইল দেখা এবং আপডেট করার জন্য সিরিয়ালাইজার"""
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
    """নতুন ইউজার সাইন-আপ করার সিরিয়ালাইজার (username বাদ দিয়ে email বেসড)"""
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
        
        # টেন্যান্ট কনটেক্সট হ্যান্ডলিং
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
    """পাসওয়ার্ড পরিবর্তন করার জন্য সিরিয়ালাইজার"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("বর্তমান পাসওয়ার্ডটি সঠিক নয়।")
        return value