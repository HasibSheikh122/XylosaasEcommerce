# apps/products/serializers.py
import uuid
from django.utils.text import slugify
from rest_framework import serializers
from .models import Category, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    """হোমপেজ বাবল ও মেন্যু ক্যাটাগরি সিরিয়ালাইজার"""
    product_count = serializers.IntegerField(source='products.count', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'icon',
            'image',
            'image_url',
            'display_order',
            'show_on_homepage',
            'product_count',
        ]
        extra_kwargs = {
            'image': {'required': False},
            'slug': {'required': False},
        }

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            url = obj.image.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None


class ProductImageSerializer(serializers.ModelSerializer):
    """গ্যালারি ইমেজ সিরিয়ালাইজার"""
    image_url = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'product_name', 'image', 'image_url', 'alt_text', 'is_primary', 'order']
        extra_kwargs = {
            'product': {'required': False}
        }

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            url = obj.image.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None


class ProductCardSerializer(serializers.ModelSerializer):
    """
    হোমপেজ গ্রিড, বেস্টসেলার এবং মার্চেন্ট টেবিলের জন্য সিরিয়ালাইজার
    """
    discount_percentage = serializers.ReadOnlyField()
    primary_image = serializers.SerializerMethodField()
    is_in_stock = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    category_id = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'unit',
            'price',
            'compare_price',
            'discount_percentage',
            'custom_badge',
            'rating',
            'total_reviews',
            'stock_quantity',
            'is_in_stock',
            'primary_image',
            'images',
            'category',
            'category_id',
            'category_name',
            'is_active',
            'is_featured',
            'is_bestseller',
            'is_deal_of_day',
        ]

    def get_primary_image(self, obj):
        request = self.context.get('request')
        url = getattr(obj, 'primary_image_url', None) or (obj.image.url if getattr(obj, 'image', None) else None)
        if url and request:
            return request.build_absolute_uri(url)
        return url

    def get_is_in_stock(self, obj):
        return (obj.stock_quantity or 0) > 0

    def get_category(self, obj):
        first_cat = obj.categories.first()
        return first_cat.id if first_cat else None

    def get_category_id(self, obj):
        first_cat = obj.categories.first()
        return first_cat.id if first_cat else None

    def get_category_name(self, obj):
        first_cat = obj.categories.first()
        return first_cat.name if first_cat else "General"

    def get_images(self, obj):
        request = self.context.get('request')
        img_qs = None
        if hasattr(obj, 'product_images'):
            img_qs = obj.product_images.all()
        elif hasattr(obj, 'images'):
            img_qs = obj.images.all()
        elif hasattr(obj, 'productimage_set'):
            img_qs = obj.productimage_set.all()

        if img_qs and img_qs.exists():
            return ProductImageSerializer(img_qs, many=True, context={'request': request}).data
        return []


ProductListSerializer = ProductCardSerializer


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    সিঙ্গেল প্রোডাক্ট ডিটেইল ও মার্চেন্ট এডিট (PATCH) হ্যান্ডলিং সিরিয়ালাইজার
    """
    discount_percentage = serializers.ReadOnlyField()
    product_images = ProductImageSerializer(many=True, read_only=True)
    images = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, read_only=True)
    category = serializers.SerializerMethodField()
    category_id = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    is_in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'unit',
            'price',
            'compare_price',
            'discount_percentage',
            'custom_badge',
            'rating',
            'total_reviews',
            'sku',
            'stock_quantity',
            'is_in_stock',
            'weight',
            'dimensions',
            'variants',
            'category',
            'category_id',
            'category_name',
            'categories',
            'product_images',
            'images',
            'primary_image',
            'meta_title',
            'meta_description',
            'is_featured',
            'is_bestseller',
            'is_deal_of_day',
            'is_active',
            'created_at',
        ]

    def get_is_in_stock(self, obj):
        return (obj.stock_quantity or 0) > 0

    def get_primary_image(self, obj):
        request = self.context.get('request')
        url = getattr(obj, 'primary_image_url', None) or (obj.image.url if getattr(obj, 'image', None) else None)
        if url and request:
            return request.build_absolute_uri(url)
        return url

    def get_category(self, obj):
        first_cat = obj.categories.first()
        return first_cat.id if first_cat else None

    def get_category_id(self, obj):
        first_cat = obj.categories.first()
        return first_cat.id if first_cat else None

    def get_category_name(self, obj):
        first_cat = obj.categories.first()
        return first_cat.name if first_cat else "General"

    def get_images(self, obj):
        request = self.context.get('request')
        img_qs = None
        if hasattr(obj, 'product_images'):
            img_qs = obj.product_images.all()
        elif hasattr(obj, 'images'):
            img_qs = obj.images.all()
        elif hasattr(obj, 'productimage_set'):
            img_qs = obj.productimage_set.all()

        if img_qs and img_qs.exists():
            return ProductImageSerializer(img_qs, many=True, context={'request': request}).data
        return []

    def update(self, instance, validated_data):
        """ক্যাটাগরি পরিবর্তন ডাটাবেজে লক করা"""
        instance = super().update(instance, validated_data)

        # ফ্রন্টএন্ড থেকে পাঠানো category অথবা category_id ধরা
        raw_cat = self.initial_data.get('category')
        if raw_cat is None:
            raw_cat = self.initial_data.get('category_id')

        if raw_cat is not None:
            if raw_cat in ['', 'null', 'None', 0, '0']:
                instance.categories.clear()
                if hasattr(instance, 'category'):
                    instance.category = None
                    instance.save(update_fields=['category'])
            else:
                try:
                    cat_obj = Category.objects.filter(id=int(raw_cat)).first()
                    if cat_obj:
                        instance.categories.clear()
                        instance.categories.add(cat_obj)
                        if hasattr(instance, 'category'):
                            instance.category = cat_obj
                            instance.save(update_fields=['category'])
                except (ValueError, TypeError):
                    pass

        return instance


class ProductCreateSerializer(serializers.ModelSerializer):
    """মার্চেন্ট অ্যাডমিন থেকে সহজে প্রোডাক্ট তৈরির সিরিয়ালাইজার"""
    image = serializers.ImageField(write_only=True, required=False)
    category_name = serializers.CharField(write_only=True, required=False, default="General")
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    stock = serializers.IntegerField(write_only=True, required=False, source='stock_quantity', default=10)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'price', 'compare_price', 'stock',
            'description', 'unit', 'image', 'category_name', 'category_id', 'sku'
        ]
        extra_kwargs = {
            'sku': {'required': False},
            'slug': {'required': False},
        }

    def create(self, validated_data):
        request = self.context.get('request')
        tenant = getattr(request, 'tenant', None) or getattr(request.user, 'tenant', None)
        image = validated_data.pop('image', None)
        category_name = validated_data.pop('category_name', 'General')
        category_id = validated_data.pop('category_id', None)

        if not validated_data.get('sku'):
            validated_data['sku'] = f"SKU-{uuid.uuid4().hex[:8].upper()}"

        validated_data['tenant'] = tenant
        product = Product.objects.create(**validated_data)

        # ক্যাটাগরি অ্যাসাইন করা
        if category_id:
            cat_obj = Category.objects.filter(id=category_id).first()
            if cat_obj:
                product.categories.add(cat_obj)
        elif category_name and tenant:
            category_slug = slugify(category_name) or "general"
            category, _ = Category.objects.get_or_create(
                tenant=tenant,
                slug=category_slug,
                defaults={'name': category_name}
            )
            product.categories.add(category)

        # প্রোডাক্ট ইমেজ তৈরি
        if image:
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=True
            )

        return product