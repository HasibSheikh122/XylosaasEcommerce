from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import ShippingZone, ShippingMethod, ShippingRate, Shipment, Carrier

@admin.register(Carrier)
class CarrierAdmin(ModelAdmin):
    list_display = ('name', 'carrier_type', 'is_active', 'is_default', 'tenant')
    list_filter = ('carrier_type', 'is_active', 'tenant')
    fieldsets = (
        ('General Information', {'fields': ('tenant', 'name', 'carrier_type', 'is_active', 'is_default')}),
        ('API Configuration', {'fields': ('api_key', 'api_secret', 'api_username', 'api_password', 'api_url')}),
        ('Tracking Info', {'fields': ('tracking_url_template', 'tracking_api_url', 'supported_services')}),
    )

@admin.register(ShippingZone)
class ShippingZoneAdmin(ModelAdmin):
    list_display = ('name', 'tenant', 'is_active', 'is_default', 'priority')
    list_filter = ('is_active', 'tenant')
    search_fields = ('name',)

@admin.register(ShippingMethod)
class ShippingMethodAdmin(ModelAdmin):
    list_display = ('name', 'carrier', 'method_type', 'base_cost', 'is_active')
    list_filter = ('method_type', 'is_active', 'carrier')
    filter_horizontal = ('zones',) # মাল্টিপল জোন সিলেক্ট করার জন্য
    fieldsets = (
        ('Basic Info', {'fields': ('tenant', 'name', 'carrier', 'method_type', 'zones', 'is_active', 'is_default')}),
        ('Pricing & Limits', {'fields': ('base_cost', 'cost_per_kg', 'cost_per_item', 'handling_fee', 'free_shipping_threshold', 'max_weight_kg', 'max_items')}),
        ('Delivery Settings', {'fields': ('delivery_days_min', 'delivery_days_max', 'tracking_required', 'is_available_for_cod')}),
    )

@admin.register(ShippingRate)
class ShippingRateAdmin(ModelAdmin):
    list_display = ('name', 'method', 'zone', 'rate', 'priority')
    list_filter = ('method', 'zone', 'tenant')

@admin.register(Shipment)
class ShipmentAdmin(ModelAdmin):
    list_display = ('shipment_number', 'order', 'status', 'carrier_name', 'tracking_number', 'created_at')
    list_filter = ('status', 'carrier_name', 'tenant', 'created_at')
    search_fields = ('shipment_number', 'tracking_number', 'order__order_number')
    readonly_fields = ('shipment_number', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Order & Carrier', {'fields': ('tenant', 'order', 'method', 'shipment_number', 'tracking_number', 'carrier_name', 'carrier_service', 'status')}),
        ('Addresses', {'fields': ('pickup_address', 'delivery_address')}),
        ('Shipping Details', {'fields': ('weight_kg', 'dimensions', 'shipping_cost', 'insurance_cost', 'cod_amount', 'signature_required')}),
        ('Timestamps', {'fields': ('shipped_at', 'expected_delivery_date', 'actual_delivery_date', 'delivered_at')}),
        ('Internal Notes', {'fields': ('notes', 'delivery_notes', 'tracking_history')}),
    )