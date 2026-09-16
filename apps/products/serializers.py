from rest_framework import serializers
from django.utils.text import slugify
from .models import Category, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    """ক্যাটাগরি ট্রি এবং সাব-ক্যাটাগরি হ্যান্ডলিং সিরিয়ালাইজার"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    products_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Category
        fields = [
            'id', 'tenant', 'name', 'slug', 'description',
            'parent', 'parent_name', 'image',
            'meta_title', 'meta_description',
            'is_active', 'products_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        tenant = getattr(request, 'tenant', None) if request else None

        # স্ল্যাগ প্রদান না করলে অটো-স্ল্যাগ তৈরি
        if not validated_data.get('slug'):
            base_slug = slugify(validated_data['name'])
            slug = base_slug
            counter = 1
            while Category.objects.filter(tenant=tenant, slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            validated_data['slug'] = slug

        if tenant:
            validated_data['tenant'] = tenant
        return super().create(validated_data)


class ProductImageSerializer(serializers.ModelSerializer):
    """প্রোডাক্ট গ্যালারি ইমেজ সিরিয়ালাইজার"""
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'alt_text', 'is_primary', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductListSerializer(serializers.ModelSerializer):
    """স্টোরফ্রন্ট গ্রিড/কার্ড ভিউয়ের জন্য লাইটওয়েট সিরিয়ালাইজার"""
    primary_image = serializers.SerializerMethodField()
    category_names = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'price', 'compare_price',
            'sku', 'stock_quantity', 'is_featured', 'is_digital',
            'primary_image', 'category_names', 'created_at'
        ]

    def get_primary_image(self, obj):
        prim = obj.product_images.filter(is_primary=True).first()
        if not prim:
            prim = obj.product_images.first()
        if prim and prim.image:
            request = self.context.get('request')
            return request.build_absolute_uri(prim.image.url) if request else prim.image.url
        # যদি JSONField images-এ URL থাকে
        if obj.images and len(obj.images) > 0:
            return obj.images[0]
        return None

    def get_category_names(self, obj):
        return [c.name for c in obj.categories.all()]


class ProductDetailSerializer(serializers.ModelSerializer):
    """প্রোডাক্ট ডিটেইল পেজ এবং অ্যাডমিন ম্যানেজমেন্টের জন্য পূর্ণাঙ্গ সিরিয়ালাইজার"""
    product_images = ProductImageSerializer(many=True, read_only=True)
    category_details = CategorySerializer(source='categories', many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'tenant', 'name', 'slug', 'description',
            'price', 'compare_price', 'cost_price',
            'sku', 'barcode', 'stock_quantity', 'low_stock_threshold',
            'weight', 'dimensions', 'variants',
            'images', 'video_url', 'product_images',
            'categories', 'category_details',
            'meta_title', 'meta_description', 'meta_keywords',
            'is_active', 'is_featured', 'is_digital',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']

    def create(self, validated_data):
        categories = validated_data.pop('categories', [])
        request = self.context.get('request')
        tenant = getattr(request, 'tenant', None) if request else None

        # অটো স্ল্যাগ জেনারেশন
        if not validated_data.get('slug'):
            base_slug = slugify(validated_data['name'])
            slug = base_slug
            counter = 1
            while Product.objects.filter(tenant=tenant, slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            validated_data['slug'] = slug

        if tenant:
            validated_data['tenant'] = tenant

        product = Product.objects.create(**validated_data)
        if categories:
            product.categories.set(categories)
        return product

    def update(self, instance, validated_data):
        categories = validated_data.pop('categories', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if categories is not None:
            instance.categories.set(categories)
        return instance