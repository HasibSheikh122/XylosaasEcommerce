from rest_framework import serializers
from .models import Carrier, ShippingZone, ShippingMethod, ShippingRate, Shipment


class CarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        fields = [
            'id', 'tenant', 'name', 'carrier_type',
            'api_key', 'api_secret', 'api_username', 'api_password', 'api_url',
            'tracking_url_template', 'tracking_api_url',
            'is_active', 'is_default', 'supported_services', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']
        extra_kwargs = {
            # এপিআই সিক্রেট ও পাসওয়ার্ড যেন রেসপন্সে লিক না হয়
            'api_secret': {'write_only': True},
            'api_password': {'write_only': True},
        }


class ShippingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingZone
        fields = [
            'id', 'tenant', 'name', 'description',
            'countries', 'states', 'cities', 'zip_codes',
            'estimated_delivery_days_min', 'estimated_delivery_days_max',
            'is_active', 'is_default', 'priority',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class ShippingMethodSerializer(serializers.ModelSerializer):
    carrier_name = serializers.CharField(source='carrier.name', read_only=True)
    method_type_display = serializers.CharField(source='get_method_type_display', read_only=True)

    class Meta:
        model = ShippingMethod
        fields = [
            'id', 'tenant', 'carrier', 'carrier_name', 'zones',
            'name', 'description', 'method_type', 'method_type_display',
            'base_cost', 'cost_per_kg', 'cost_per_item', 'handling_fee',
            'free_shipping_threshold', 'max_weight_kg', 'max_items',
            'delivery_days_min', 'delivery_days_max',
            'tracking_url', 'tracking_required',
            'is_active', 'is_default', 'is_available_for_cod', 'priority',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class ShippingRateSerializer(serializers.ModelSerializer):
    method_name = serializers.CharField(source='method.name', read_only=True)
    zone_name = serializers.CharField(source='zone.name', read_only=True)

    class Meta:
        model = ShippingRate
        fields = [
            'id', 'tenant', 'method', 'method_name', 'zone', 'zone_name',
            'name', 'rate',
            'min_weight_kg', 'max_weight_kg', 'min_order_value', 'max_order_value',
            'priority', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class ShipmentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'id', 'tenant', 'order', 'order_number', 'method',
            'shipment_number', 'tracking_number', 'carrier_name', 'carrier_service',
            'status', 'status_display', 'pickup_address', 'delivery_address',
            'expected_delivery_date', 'actual_delivery_date', 'shipped_at', 'delivered_at',
            'weight_kg', 'dimensions', 'shipping_cost', 'insurance_cost', 'cod_amount',
            'tracking_history', 'signature_required', 'signature_photo',
            'notes', 'delivery_notes', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'tracking_history', 'created_at', 'updated_at']


class CalculateShippingSerializer(serializers.Serializer):
    """চেকআউটে শিপিং চার্জ হিসাব করার জন্য রিকোয়েস্ট ভ্যালিডেশন"""
    weight_kg = serializers.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    item_count = serializers.IntegerField(default=1)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    address = serializers.DictField(required=False, default=dict)


class TrackingUpdateSerializer(serializers.Serializer):
    """শিপমেন্ট ট্র্যাকিং আপডেট দেওয়ার জন্য ভ্যালিডেশন"""
    status = serializers.ChoiceField(choices=Shipment.STATUS_CHOICES)
    description = serializers.CharField(max_length=255)
    location = serializers.CharField(max_length=150, required=False, allow_blank=True)