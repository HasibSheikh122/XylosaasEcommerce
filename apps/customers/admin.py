from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    # লিস্ট ভিউতে যা যা দেখা যাবে
    list_display = ('first_name', 'last_name', 'email', 'tenant', 'total_orders', 'lifetime_value', 'churn_risk')
    
    # ফিল্টার করার অপশন
    list_filter = ('tenant', 'customer_segment', 'email_opt_in', 'sms_opt_in')
    
    # সার্চ অপশন
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'tenant__store_name')
    
    # ফিল্ডগুলোর বিন্যাস (Fieldsets)
    fieldsets = (
        ('Basic Information', {
            'fields': ('tenant', 'user', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Addresses (JSON)', {
            'fields': ('default_shipping_address', 'default_billing_address', 'saved_addresses'),
            'classes': ('collapse',) # এটাকে কলাপস করে রাখা হয়েছে যেন জায়গা কম নেয়
        }),
        ('Performance & Metrics', {
            'fields': ('total_orders', 'total_spent', 'last_order_date', 'lifetime_value')
        }),
        ('AI & Marketing', {
            'fields': ('customer_segment', 'churn_risk', 'email_opt_in', 'sms_opt_in', 'tags')
        }),
        ('Additional Notes', {
            'fields': ('notes',)
        }),
    )

    # রিড-অনলি ফিল্ডস (সিস্টেম জেনারেটেড ডেটা)
    readonly_fields = ('created_at', 'updated_at', 'last_order_date')

    # সাজানোর সুবিধা
    ordering = ('-created_at',)