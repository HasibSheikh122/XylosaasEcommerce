from rest_framework import viewsets, permissions
from .models import Category, Product, ProductImage
from .serializers import CategorySerializer, ProductSerializer, ProductImageSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # শুধুমাত্র বর্তমান ট্যানেন্ট-এর ক্যাটাগরিগুলো রিটার্ন করবে
        return self.queryset.filter(tenant=self.request.user.tenant)

    def perform_create(self, serializer):
        # নতুন ক্যাটাগরি তৈরি করার সময় স্বয়ংক্রিয়ভাবে বর্তমান ট্যানেন্ট অ্যাসাইন হয়ে যাবে
        serializer.save(tenant=self.request.user.tenant)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # শুধুমাত্র বর্তমান ট্যানেন্ট-এর প্রোডাক্টগুলো রিটার্ন করবে
        return self.queryset.filter(tenant=self.request.user.tenant)

    def perform_create(self, serializer):
        # নতুন প্রোডাক্ট তৈরি করার সময় স্বয়ংক্রিয়ভাবে বর্তমান ট্যানেন্ট অ্যাসাইন হয়ে যাবে
        serializer.save(tenant=self.request.user.tenant)


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # ইমেজ যে প্রোডাক্টের আন্ডারে, সেই প্রোডাক্টটি বর্তমান ট্যানেন্টের কিনা তা যাচাই করবে
        return self.queryset.filter(product__tenant=self.request.user.tenant)