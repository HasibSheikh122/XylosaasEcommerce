from django.contrib import admin
from .models import Plan, Subscription

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    # CSS লোড করার জন্য Media ক্লাস
    class Media:
        css = {
            'all': ('css/admin-custom.css',)
        }
    # ১. প্ল্যানগুলোর তালিকা দেখার সময় যে কলামগুলো সামনে থাকবে
    list_display = ('display_name', 'name', 'monthly_price', 'yearly_price', 'max_products', 'is_active')
    
    # ২. ফিল্টার করার সুবিধা
    list_filter = ('is_active', 'name', 'custom_domain')
    
    # ৩. সার্চ অপশন
    search_fields = ('display_name', 'name')
    
    # ৪. প্ল্যানের ভেতরে ফিল্ডগুলো সুন্দর করে সাজানো (Fieldsets)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'description', 'is_active')
        }),
        ('Plan Limits (Core Features)', {
            'fields': ('max_products', 'max_staff', 'max_orders_per_month', 'custom_domain'),
            'description': 'Define the limits for merchants on this plan.'
        }),
        ('AI Superpowers 🚀', {
            'classes': ('collapse',),  # এটি অ্যাডমিনে ডিফল্টভাবে হাইড থাকবে, ক্লিক করলে এক্সপ্যান্ড হবে
            'fields': (
                'ai_recommendation', 'ai_search', 'ai_chatbot', 'ai_analytics',
                'ai_demand_forecast', 'ai_dynamic_pricing', 'ai_customer_segmentation',
                'ai_churn_prediction', 'ai_fraud_detection', 'ai_content_generator'
            ),
            'description': 'Toggle advanced AI capabilities for this plan layer.'
        }),
        ('Pricing Config', {
            'fields': ('monthly_price', 'yearly_price', 'setup_fee')
        }),
    )

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Subscription Status', {
            # সরাসরি Tailwind এর ক্লাস ব্যবহার করুন
            'classes': ('flex', 'items-center', 'p-4', 'bg-emerald-50', 'rounded-lg', 'shadow-md'),
            'fields': ('status',),
        }),
    )
    # CSS লোড করার জন্য Media ক্লাস
    class Media:
        css = {
            'all': ('css/admin-custom.css',)
        }
    # ১. সাবস্ক্রিপশনের মেইন টেবিলে যা যা দেখতে চান
    list_display = ('tenant', 'plan', 'status', 'current_period_end', 'payment_provider', 'created_at')
    
    # ২. স্ট্যাটাস এবং প্ল্যান দিয়ে দ্রুত ফিল্টার করার ব্যবস্থা
    list_filter = ('status', 'plan', 'payment_provider', 'created_at')
    
    # ৩. টেন্যান্ট বা স্টোরের নাম দিয়ে সার্চ করার সুবিধা
    search_fields = ('tenant__store_name', 'payment_provider_id')  # ধরে নেওয়া হয়েছে Tenant মডেলে store_name আছে
    
    # ৪. ডেট বা তারিখ ফিল্টার করার জন্য টাইমলাইন
    date_hierarchy = 'current_period_end'
    
    # ৫. সাবস্ক্রিপশন ডিটেইলসের লেআউট
    fieldsets = (
        ('Relations', {
            'fields': ('tenant', 'plan')
        }),
        ('Subscription Status', {
            'fields': ('status',)
        }),
        ('Important Billing Cycles', {
            'fields': (('trial_start', 'trial_end'), ('current_period_start', 'current_period_end'), 'canceled_at'),
        }),
        ('Payment Gateway Details', {
            'fields': ('payment_provider', 'payment_provider_id'),
        }),
    )
    
    # কিছু মেটাডেটা যা ভুল করে এডিট করা ঠিক হবে না
    readonly_fields = ('created_at', 'updated_at')