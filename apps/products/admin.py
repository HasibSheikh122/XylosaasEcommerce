from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline
from .models import Category, Product, ProductImage
from django_tenants.admin import TenantAdminMixin # যদি প্রয়োজন হয়
from apps.tenants.models import Tenant

class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1  # নতুন ইমেজ যোগ করার জন্য একটি খালি সারি
    fields = ('image', 'alt_text', 'is_primary', 'order')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'parent', 'is_active')
    list_filter = ('tenant', 'is_active')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    # এই মেথডটি নিশ্চিত করবে যে ড্রপডাউনে অন্য টেন্যান্ট দেখা যাবে না
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tenant":
            # শুধুমাত্র বর্তমান টেন্যান্টকে ফিল্টার করবে
            kwargs["queryset"] = Tenant.objects.filter(id=request.tenant.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # এটি নিশ্চিত করবে যে টেন্যান্ট ফিল্ডটি অটোমেটিক সেট হয়ে যাবে
    def save_model(self, request, obj, form, change):
        if not obj.tenant_id:
            obj.tenant = request.tenant
        super().save_model(request, obj, form, change)

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('name', 'tenant', 'sku', 'price', 'stock_quantity', 'is_active', 'is_featured')
    list_filter = ('tenant', 'is_active', 'is_featured', 'categories')
    search_fields = ('name', 'sku', 'barcode')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    
    # টেন্যান্ট ফিল্ডটি হাইড করতে চাইলে (যদি আপনি চান অটোমেটিক সেট হোক)
    # exclude = ('tenant',) 

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # টেন্যান্ট ফিল্টারিং
        if db_field.name == "tenant":
            kwargs["queryset"] = Tenant.objects.filter(id=request.tenant.id)
        
        # ক্যাটাগরি ফিল্টারিং (যাতে অন্য শপের ক্যাটাগরি না আসে)
        if db_field.name == "categories":
            kwargs["queryset"] = Category.objects.filter(tenant=request.tenant)
            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # এটি মাল্টিপল সিলেক্ট ফিল্ডের জন্য (যেমন ManyToManyField)
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "categories":
            kwargs["queryset"] = Category.objects.filter(tenant=request.tenant)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.tenant_id:
            obj.tenant = request.tenant
        super().save_model(request, obj, form, change)

@admin.register(ProductImage)
class ProductImageAdmin(ModelAdmin):
    list_display = ('product', 'image', 'is_primary', 'order')