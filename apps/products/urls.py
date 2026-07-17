from django.urls import path
from .views import CategoryViewSet, ProductViewSet, ProductImageViewSet

app_name = 'products'

# Category view mappings
category_list = CategoryViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
category_detail = CategoryViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

# Product view mappings
product_list = ProductViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
product_detail = ProductViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

# Product Image view mappings
product_image_list = ProductImageViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
product_image_detail = ProductImageViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

# URL patterns using explicit paths
urlpatterns = [
    # Category URLs
    path('categories/', category_list, name='category-list'),
    path('categories/<int:pk>/', category_detail, name='category-detail'),

    # Product URLs
    path('products/', product_list, name='product-list'),
    path('products/<int:pk>/', product_detail, name='product-detail'),

    # Product Image URLs
    path('product-images/', product_image_list, name='product-image-list'),
    path('product-images/<int:pk>/', product_image_detail, name='product-image-detail'),
]