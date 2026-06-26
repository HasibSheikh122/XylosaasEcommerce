from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline
from .models import Order, OrderItem

class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0  # ডিফল্টভাবে খালি সারি দেখাবে না
    readonly_fields = ('product_name', 'product_sku', 'unit_price', 'total_price', 'tax')
    can_delete = False  # অর্ডার আইটেম সাধারণত ডিলিট করা উচিত নয়

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('order_number', 'tenant', 'customer', 'status', 'payment_status', 'total', 'created_at')
    list_filter = ('status', 'payment_status', 'tenant', 'created_at')
    search_fields = ('order_number', 'customer__email', 'tracking_number')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Details', {
            'fields': ('tenant', 'customer', 'order_number', 'status', 'notes')
        }),
        ('Financials', {
            'fields': ('subtotal', 'tax', 'shipping_cost', 'discount', 'total')
        }),
        ('Shipping Information', {
            'fields': ('shipping_method', 'tracking_number', 'shipped_at', 'delivered_at', 'shipping_address'),
            'classes': ('collapse',)
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status', 'payment_id'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'order_number')

@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = ('order', 'product_name', 'quantity', 'unit_price', 'total_price')
    list_filter = ('order__tenant',)
    search_fields = ('order__order_number', 'product_name', 'product_sku')