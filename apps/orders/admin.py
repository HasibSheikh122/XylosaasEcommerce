from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline
from .models import Order, OrderItem, Cart, CartItem, Checkout, CheckoutLog

# ==========================================
# ORDER INLINES & ADMIN
# ==========================================

class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'product_sku', 'unit_price', 'total_price', 'tax')
    can_delete = False

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('order_number', 'tenant', 'customer', 'status', 'payment_status', 'total', 'created_at')
    list_filter = ('status', 'payment_status', 'tenant', 'created_at')
    search_fields = ('order_number', 'customer__email', 'tracking_number')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Details', {'fields': ('tenant', 'customer', 'order_number', 'status', 'notes')}),
        ('Financials', {'fields': ('subtotal', 'tax', 'shipping_cost', 'discount', 'total')}),
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

# ==========================================
# CART INLINES & ADMIN
# ==========================================

class CartItemInline(TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product_name', 'product_sku', 'unit_price')

@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ('id', 'tenant', 'customer', 'status', 'grand_total', 'created_at')
    list_filter = ('status', 'tenant', 'created_at')
    search_fields = ('cart_token', 'session_id', 'customer__email')
    inlines = [CartItemInline]
    readonly_fields = ('created_at', 'updated_at', 'cart_token')

# ==========================================
# CHECKOUT ADMIN
# ==========================================

@admin.register(Checkout)
class CheckoutAdmin(ModelAdmin):
    list_display = ('id', 'customer_name', 'status', 'payment_method', 'payment_status', 'grand_total', 'created_at')
    list_filter = ('status', 'payment_status', 'payment_method', 'tenant')
    search_fields = ('customer_name', 'customer_email', 'customer_phone', 'order__order_number')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')

@admin.register(CheckoutLog)
class CheckoutLogAdmin(ModelAdmin):
    list_display = ('checkout', 'log_type', 'step', 'created_at')
    list_filter = ('log_type', 'created_at')
    search_fields = ('message', 'checkout__id')
    readonly_fields = ('created_at',)