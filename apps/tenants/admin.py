from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline
from apps.tenants.models import Tenant, Domain

class DomainInline(TabularInline):
    model = Domain
    extra = 1
    classes = ('collapse',) # ডিফল্টভাবে হাইড থাকবে
    fields = ['domain', 'is_primary']

@admin.register(Tenant)
class TenantAdmin(ModelAdmin):
    # CSS লোড করার জন্য
    class Media:
        css = {
            'all': ('css/admin-custom.css',)
        }

    inlines = [DomainInline]
    
    # লিস্ট ভিউতে ব্যাজ ও স্টাইল ব্যবহার
    list_display = [
        'store_name', 
        'subdomain', 
        'plan', 
        'is_active_badge', 
        'is_trial_badge', 
        'subscription_end_date'
    ]
    
    list_filter = ['is_active', 'is_trial', 'plan', 'created_at']
    search_fields = ['store_name', 'subdomain', 'schema_name']
    
    # UI লেআউট অপ্টিমাইজেশন
    fieldsets = (
        (None, {
            'fields': (('store_name', 'subdomain', 'schema_name'), 'is_active')
        }),
        ('Subscription & Plans', {
            'classes': ('collapse',),
            'fields': ('plan', 'is_trial', ('trial_ends_at', 'subscription_end_date'))
        }),
        ('Store Customization', {
            'classes': ('collapse',),
            'fields': ('logo', 'favicon', 'custom_domain')
        }),
        ('AI & Resource Limits', {
            'classes': ('collapse',),
            'fields': ('max_products', 'max_staff', 'max_orders_per_month', 'ai_enabled', 'ai_features')
        }),
    )

    # লজিক্যাল ব্যাজ তৈরি (Unfold-এ এটি চমৎকার দেখায়)
    @admin.display(description="Status", boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active
    
    @admin.display(description="Trial", boolean=True)
    def is_trial_badge(self, obj):
        return obj.is_trial

@admin.register(Domain)
class DomainAdmin(ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['domain', 'tenant__store_name']