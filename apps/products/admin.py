from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline
from .models import Category, Product, ProductImage

class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1  # নতুন ইমেজ যোগ করার জন্য একটি খালি সারি
    fields = ('image', 'alt_text', 'is_primary', 'order')

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'tenant', 'parent', 'is_active')
    list_filter = ('tenant', 'is_active')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}  # স্লাগ অটোমেটিক তৈরি হবে

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('name', 'tenant', 'sku', 'price', 'stock_quantity', 'is_active', 'is_featured')
    list_filter = ('tenant', 'is_active', 'is_featured', 'categories')
    search_fields = ('name', 'sku', 'barcode')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]  # একই পেজে ইমেজ ম্যানেজমেন্ট
    
    fieldsets = (
        ('General Information', {
            'fields': ('tenant', 'name', 'slug', 'description', 'categories')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'compare_price', 'cost_price', 'sku', 'barcode', 'stock_quantity', 'low_stock_threshold')
        }),
        ('Attributes & Status', {
            'fields': ('weight', 'dimensions', 'variants', 'is_active', 'is_featured', 'is_digital')
        }),
        ('SEO & AI', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'ai_embedding', 'ai_metadata'),
            'classes': ('collapse',)  # AI ফিল্ডগুলো ডিফল্টভাবে কলাপস থাকবে
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ProductImage)
class ProductImageAdmin(ModelAdmin):
    list_display = ('product', 'image', 'is_primary', 'order')