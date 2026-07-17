from rest_framework import serializers
from .models import Category, Product, ProductImage

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'
        read_only_fields = ('created_at',)

class ProductSerializer(serializers.ModelSerializer):
    # নেস্টেড ইমেজেস রিড-অনলি হিসেবে দেখার জন্য
    product_images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')