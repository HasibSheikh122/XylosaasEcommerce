# apps/products/views.py
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import django_filters

from .models import Category, Product, ProductImage
from .serializers import (
    CategorySerializer,
    ProductCardSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductImageSerializer,
    ProductCreateSerializer,
)


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    category = django_filters.CharFilter(field_name="categories__slug", lookup_expr='exact')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')

    class Meta:
        model = Product
        fields = ['is_featured', 'is_bestseller', 'is_deal_of_day', 'is_active', 'categories']

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock_quantity__gt=0)
        return queryset.filter(stock_quantity=0)


class CategoryViewSet(viewsets.ModelViewSet):
    """Category management ebong storefront bubble grid view"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'show_on_homepage', 'parent']
    search_fields = ['name', 'description']
    ordering_fields = ['display_order', 'name']
    ordering = ['display_order', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = getattr(self.request, 'tenant', None)
        if tenant:
            qs = qs.filter(tenant=tenant)
        if not (self.request.user and self.request.user.is_authenticated):
            qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        serializer.save(tenant=tenant)

    def perform_update(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        if tenant:
            serializer.save(tenant=tenant)
        else:
            serializer.save()


class ProductViewSet(viewsets.ModelViewSet):
    """Product catalog ebong inventory management viewset"""
    queryset = Product.objects.prefetch_related('categories', 'product_images').all()
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'sku', 'barcode', 'description', 'meta_keywords']
    ordering_fields = ['price', 'created_at', 'stock_quantity', 'rating', 'name']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'featured', 'bestsellers', 'deals_of_the_day', 'home_sections']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = getattr(self.request, 'tenant', None)
        if tenant:
            qs = qs.filter(tenant=tenant)

        if not (self.request.user and self.request.user.is_authenticated):
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return ProductCreateSerializer
        if self.action in ['list', 'featured', 'bestsellers', 'deals_of_the_day']:
            return ProductCardSerializer
        return ProductDetailSerializer

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        serializer.save(tenant=tenant)

    def perform_update(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        if tenant:
            instance = serializer.save(tenant=tenant)
        else:
            instance = serializer.save()

        # 🌟 ব্যাকএন্ড লেভেলে ক্যাটাগরি নিশ্চিত আপডেট করা
        raw_cat = self.request.data.get('category')
        if raw_cat is None:
            raw_cat = self.request.data.get('category_id')

        if raw_cat is not None:
            if raw_cat in ['', 'null', 'None', 0, '0']:
                instance.categories.clear()
                if hasattr(instance, 'category'):
                    instance.category = None
                    instance.save(update_fields=['category'])
            else:
                try:
                    cat = Category.objects.filter(id=int(raw_cat)).first()
                    if cat:
                        instance.categories.clear()
                        instance.categories.add(cat)
                        if hasattr(instance, 'category'):
                            instance.category = cat
                            instance.save(update_fields=['category'])
                except (ValueError, TypeError):
                    pass

    # ==========================================
    # Product Image Actions
    # ==========================================

    @action(detail=True, methods=['post'], url_path='upload-image', parser_classes=[MultiPartParser, FormParser])
    def upload_image(self, request, pk=None):
        product = self.get_object()
        file_obj = request.FILES.get('image')

        if not file_obj:
            return Response({"detail": "Kono image file select kora hoyni."}, status=status.HTTP_400_BAD_REQUEST)

        is_first = not product.product_images.exists()
        new_image = ProductImage.objects.create(
            product=product,
            image=file_obj,
            is_primary=is_first
        )

        serializer = ProductImageSerializer(new_image, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'], url_path='images', parser_classes=[MultiPartParser, FormParser])
    def manage_images(self, request, pk=None):
        product = self.get_object()

        if request.method == 'GET':
            images = product.product_images.all().order_by('-is_primary', 'order', 'created_at')
            serializer = ProductImageSerializer(images, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            file_obj = request.FILES.get('image')
            if not file_obj:
                return Response({"detail": "Image file paoa jayni."}, status=status.HTTP_400_BAD_REQUEST)

            is_primary = request.data.get('is_primary') in [True, 'true', 'True', 1, '1']
            if is_primary or not product.product_images.exists():
                product.product_images.update(is_primary=False)
                is_primary = True

            new_image = ProductImage.objects.create(
                product=product,
                image=file_obj,
                is_primary=is_primary
            )
            serializer = ProductImageSerializer(new_image, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'images/(?P<image_id>\d+)')
    def delete_image(self, request, pk=None, image_id=None):
        product = self.get_object()
        image = get_object_or_404(ProductImage, id=image_id, product=product)

        was_primary = image.is_primary
        image.delete()

        if was_primary:
            first = product.product_images.first()
            if first:
                first.is_primary = True
                first.save()

        return Response({"message": "Image delete shomponno hoyeche."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path=r'images/(?P<image_id>\d+)/set-primary')
    def set_primary_image(self, request, pk=None, image_id=None):
        product = self.get_object()
        image = get_object_or_404(ProductImage, id=image_id, product=product)

        product.product_images.update(is_primary=False)
        image.is_primary = True
        image.save()

        return Response({"message": "Cover image set kora hoyeche."}, status=status.HTTP_200_OK)

    # ==========================================
    # Storefront & Marketing Section Endpoints
    # ==========================================

    @action(detail=False, methods=['get'], url_path='home-sections')
    def home_sections(self, request):
        qs = self.get_queryset()
        context = {'request': request}

        cat_qs = Category.objects.filter(is_active=True)
        if hasattr(request, 'tenant') and request.tenant:
            cat_qs = cat_qs.filter(tenant=request.tenant)
        categories = cat_qs.filter(show_on_homepage=True).order_by('display_order')[:10]

        featured = qs.filter(is_featured=True, is_active=True)[:8]
        bestsellers = qs.filter(is_bestseller=True, is_active=True)[:8]
        deals = qs.filter(is_deal_of_day=True, is_active=True)[:4]

        return Response({
            'categories': CategorySerializer(categories, many=True, context=context).data,
            'featured_products': ProductCardSerializer(featured, many=True, context=context).data,
            'bestseller_products': ProductCardSerializer(bestsellers, many=True, context=context).data,
            'deals_of_the_day': ProductCardSerializer(deals, many=True, context=context).data,
        })

    @action(detail=False, methods=['get'], url_path='deals-of-the-day')
    def deals_of_the_day(self, request):
        products = self.get_queryset().filter(is_deal_of_day=True, is_active=True)[:10]
        serializer = ProductCardSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='featured')
    def featured(self, request):
        products = self.get_queryset().filter(is_featured=True, is_active=True)[:10]
        serializer = ProductCardSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='bestsellers')
    def bestsellers(self, request):
        products = self.get_queryset().filter(is_bestseller=True, is_active=True)[:10]
        serializer = ProductCardSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.select_related('product').all()
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, 'tenant') and self.request.tenant:
            qs = qs.filter(product__tenant=self.request.tenant)
        return qs