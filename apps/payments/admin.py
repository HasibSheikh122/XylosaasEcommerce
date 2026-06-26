from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline
from .models import PaymentGateway, PaymentTransaction, PaymentSubscription, PaymentRefund, PaymentLog

class PaymentTransactionInline(TabularInline):
    model = PaymentTransaction
    extra = 0
    readonly_fields = ('transaction_id', 'amount', 'status', 'initiated_at')
    can_delete = False

@admin.register(PaymentGateway)
class PaymentGatewayAdmin(ModelAdmin):
    list_display = ('gateway_type', 'tenant', 'is_active', 'is_default')
    list_filter = ('is_active', 'gateway_type', 'tenant')
    fieldsets = (
        ('General Settings', {'fields': ('tenant', 'gateway_type', 'is_active', 'is_default')}),
        ('API Credentials', {'fields': ('api_key', 'api_secret', 'api_username', 'api_password')}),
        ('Fees Structure', {'fields': ('transaction_fee_percentage', 'transaction_fee_fixed')}),
        ('Advanced Configuration', {'fields': ('gateway_settings',), 'classes': ('collapse',)}),
    )

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(ModelAdmin):
    list_display = ('transaction_id', 'tenant', 'order', 'amount', 'status', 'payment_method', 'initiated_at')
    list_filter = ('status', 'payment_method', 'tenant', 'initiated_at')
    search_fields = ('transaction_id', 'gateway_transaction_id', 'order__order_number', 'customer_email')
    readonly_fields = ('transaction_id', 'initiated_at', 'gateway_response')
    
    fieldsets = (
        ('Transaction Info', {'fields': ('tenant', 'order', 'customer', 'transaction_id', 'status')}),
        ('Financials', {'fields': ('amount', 'currency', 'tax_amount', 'fee_amount', 'net_amount')}),
        ('Gateway Details', {'fields': ('gateway', 'gateway_transaction_id', 'gateway_response', 'gateway_error')}),
        ('Customer & Card', {'fields': ('customer_name', 'customer_email', 'card_brand', 'card_last_four')}),
    )

@admin.register(PaymentSubscription)
class PaymentSubscriptionAdmin(ModelAdmin):
    list_display = ('tenant', 'plan_name', 'amount_paid', 'status', 'period_start', 'period_end')
    list_filter = ('status', 'billing_cycle', 'tenant')
    search_fields = ('plan_name', 'tenant__store_name')

@admin.register(PaymentRefund)
class PaymentRefundAdmin(ModelAdmin):
    list_display = ('refund_transaction_id', 'transaction', 'refund_amount', 'status', 'is_approved')
    list_filter = ('status', 'is_approved', 'refund_reason')
    readonly_fields = ('refund_transaction_id', 'created_at')

@admin.register(PaymentLog)
class PaymentLogAdmin(ModelAdmin):
    list_display = ('log_type', 'tenant', 'created_at', 'error_code')
    list_filter = ('log_type', 'created_at')
    search_fields = ('error_message', 'log_data')
    readonly_fields = ('log_data', 'response_data', 'created_at')