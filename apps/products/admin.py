from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    """প্রোডাক্ট পেজের নিচেই একসাথে একাধিক ছবি আপলোডের সুবিধা"""
    model = ProductImage
    extra = 1
    fields = ('image', 'preview', 'alt_text', 'is_primary', 'order')
    readonly_fields = ('preview',)

    def preview(self, instance):
        if instance.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px;" />',
                instance.image.url
            )
        return "No Image"
    preview.short_description = "Preview"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'icon_display',
        'slug',
        'parent',
        'display_order',
        'show_on_homepage',
        'is_active',
    )
    list_editable = ('display_order', 'show_on_homepage', 'is_active')
    list_filter = ('is_active', 'show_on_homepage')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('display_order', 'name')

    def icon_display(self, obj):
        return obj.icon if obj.icon else "—"
    icon_display.short_description = "Icon"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'unit',
        'price',
        'compare_price',
        'stock_quantity',
        'rating',
        'is_featured',
        'is_bestseller',
        'is_deal_of_day',
        'is_active',
    )
    list_editable = (
        'price',
        'compare_price',
        'stock_quantity',
        'is_featured',
        'is_bestseller',
        'is_deal_of_day',
        'is_active',
    )
    list_filter = (
        'is_active',
        'is_featured',
        'is_bestseller',
        'is_deal_of_day',
        'categories',
    )
    search_fields = ('name', 'sku', 'barcode')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('categories',)
    inlines = [ProductImageInline]

    fieldsets = (
        ('General Information', {
            'fields': ('tenant', 'name', 'slug', 'description', 'categories')
        }),
        ('Pricing & Grocery Measurement', {
            'fields': (
                ('price', 'compare_price', 'cost_price'),
                ('unit', 'custom_badge'),
            ),
            'description': 'গ্রোসারি কার্ডের রেট এবং ওজন (যেমন: 500 g, 1 kg) এখানে সেট করুন।'
        }),
        ('Inventory & Stock', {
            'fields': (
                ('sku', 'barcode'),
                ('stock_quantity', 'low_stock_threshold'),
            )
        }),
        ('Theme & Homepage Showcase', {
            'fields': (
                ('is_featured', 'is_bestseller', 'is_deal_of_day'),
                ('rating', 'total_reviews'),
                ('is_active', 'is_digital'),
            ),
            'description': 'হোমপেজের নির্দিষ্ট সেকশন ও রেটিং প্রদর্শন নিয়ন্ত্রণ করুন।'
        }),
        ('Dimensions & Logistics', {
            'classes': ('collapse',),
            'fields': ('weight', 'dimensions', 'variants'),
        }),
        ('SEO & Meta', {
            'classes': ('collapse',),
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
        }),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'preview', 'is_primary', 'order', 'created_at')
    list_filter = ('is_primary',)
    list_editable = ('is_primary', 'order')
    search_fields = ('product__name', 'alt_text')

    def preview(self, instance):
        if instance.image:
            return format_html(
                '<img src="{}" style="width: 45px; height: 45px; object-fit: cover; border-radius: 6px;" />',
                instance.image.url
            )
        return "No Image"
    preview.short_description = "Preview"