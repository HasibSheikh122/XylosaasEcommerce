from rest_framework import serializers
from .models import StoreSettings, StoreCategory, StorePage

# ১. ক্যাটাগরির জন্য অ্যাডভান্সড সিরিয়ালাইজার
class StoreCategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.ReadOnlyField(source='parent.name')
    is_leaf = serializers.SerializerMethodField() # চাইল্ড ক্যাটাগরি আছে কি না বোঝার জন্য

    class Meta:
        model = StoreCategory
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')

    def get_is_leaf(self, obj):
        return not obj.storecategory_set.exists()

    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("নামটি খুব ছোট, অন্তত ২ অক্ষরের হতে হবে।")
        return value

# ২. স্টোর পেজের জন্য অ্যাডভান্সড সিরিয়ালাইজার
class StorePageSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='created_by.get_full_name')
    url_path = serializers.SerializerMethodField()

    class Meta:
        model = StorePage
        fields = '__all__'
        read_only_fields = ('tenant', 'created_by', 'created_at', 'updated_at')

    def get_url_path(self, obj):
        return f"/{obj.tenant.subdomain}/page/{obj.slug}/"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # যদি ড্রাফট হয় তবে কন্টেন্ট হাইড করতে পারেন
        if not instance.is_published:
            data['content'] = "Content hidden (Draft Mode)"
        return data

# ৩. স্টোর সেটিংসের জন্য প্রোডাকশন-রেডি সিরিয়ালাইজার
class StoreSettingsSerializer(serializers.ModelSerializer):
    # JSON ফিল্ডগুলো সহজে হ্যান্ডেল করার জন্য
    full_address = serializers.SerializerMethodField()

    class Meta:
        model = StoreSettings
        exclude = ('tenant',)
        read_only_fields = ('created_at', 'updated_at')

    def get_full_address(self, obj):
        # JSONField থেকে ক্লিন অ্যাড্রেস ফরম্যাট তৈরি
        addr = obj.contact_address
        return f"{addr.get('street', '')}, {addr.get('city', '')}, {addr.get('zip', '')}"

    def validate(self, data):
        # একাধিক ফিল্ডের মধ্যে ক্রস-ভ্যালিডেশন
        if data.get('enable_online_payment') and not data.get('contact_email'):
            raise serializers.ValidationError({"contact_email": "অনলাইন পেমেন্ট চালু করতে ইমেইল আবশ্যক।"})
        return data

    def update(self, instance, validated_data):
        # সেটিংস আপডেট হওয়ার সময় কোনো লগ বা ইভেন্ট ট্রিগার করা
        instance = super().update(instance, validated_data)
        # এখানে আপনি চাইলে Cache clear করার লজিক বসাতে পারেন
        return instance