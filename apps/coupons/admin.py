from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline
from .models import Coupon, CouponUsage, CouponRule, CouponCategory

# CouponRule কে কুপনের ভেতরে ইনলাইন হিসেবে ব্যবহার করার জন্য
class CouponRuleInline(TabularInline):
    model = CouponRule
    extra = 1
    fields = ('rule_type', 'rule_value', 'is_required', 'order')

@admin.register(Coupon)
class CouponAdmin(ModelAdmin):
    list_display = ('code', 'name', 'discount_type', 'status', 'valid_from', 'valid_to', 'used_count', 'usage_limit')
    list_filter = ('status', 'discount_type', 'tenant', 'valid_to')
    search_fields = ('code', 'name', 'tenant__store_name')
    inlines = [CouponRuleInline]
    
    # ফিল্ডগুলোকে গ্রুপ করে সুন্দর দেখানোর জন্য
    fieldsets = (
        ('Basic Information', {
            'fields': ('tenant', 'code', 'name', 'description', 'status')
        }),
        ('Discount Configuration', {
            'fields': ('discount_type', 'discount_value', 'max_discount_amount', 
                       'buy_quantity', 'get_quantity', 'get_discount_percentage')
        }),
        ('Scope & Restrictions', {
            'fields': ('apply_to', 'applicable_categories', 'applicable_products', 
                       'excluded_products', 'minimum_order_amount', 'maximum_order_amount')
        }),
        ('Usage & Timing', {
            'fields': ('usage_limit', 'per_user_limit', 'valid_from', 'valid_to', 
                       'new_customers_only', 'first_order_only', 'applicable_customer_segments')
        }),
        ('Display & Stacking', {
            'fields': ('show_on_checkout', 'is_public', 'can_combine', 'priority', 'created_by')
        }),
    )
    readonly_fields = ('used_count', 'created_at', 'updated_at')

@admin.register(CouponUsage)
class CouponUsageAdmin(ModelAdmin):
    list_display = ('coupon', 'order', 'customer', 'discount_amount', 'used_at')
    list_filter = ('used_at', 'is_refunded')
    search_fields = ('coupon__code', 'order__order_number', 'customer__email')
    readonly_fields = ('used_at',)

@admin.register(CouponRule)
class CouponRuleAdmin(ModelAdmin):
    list_display = ('coupon', 'rule_type', 'is_required', 'order')
    list_filter = ('rule_type', 'coupon')

@admin.register(CouponCategory)
class CouponCategoryAdmin(ModelAdmin):
    list_display = ('name', 'tenant', 'is_active', 'color')
    list_filter = ('is_active', 'tenant')
    search_fields = ('name',)