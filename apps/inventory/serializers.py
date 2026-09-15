from rest_framework import serializers
from .models import Inventory


class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            'id',
            'tenant',
            'product',
            'product_name',
            'stock_quantity',
            'reserved_quantity',
            'available_quantity',
            'low_stock_threshold',
            'warehouse_location',
            'shelf_location',
            'bin_number',
            'reorder_point',
            'reorder_quantity',
            'last_restock_date',
            'in_transit_quantity',
            'damaged_quantity',
            'forecast_demand',
            'optimal_stock',
            'is_low_stock',
            'updated_at',
        ]
        read_only_fields = ['id', 'tenant', 'available_quantity', 'updated_at']

    def get_is_low_stock(self, obj):
        return obj.available_quantity <= obj.low_stock_threshold

    def create(self, validated_data):
        # available_quantity = stock_quantity - reserved_quantity
        stock = validated_data.get('stock_quantity', 0)
        reserved = validated_data.get('reserved_quantity', 0)
        validated_data['available_quantity'] = max(0, stock - reserved)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        stock = validated_data.get('stock_quantity', instance.stock_quantity)
        reserved = validated_data.get('reserved_quantity', instance.reserved_quantity)
        validated_data['available_quantity'] = max(0, stock - reserved)
        return super().update(instance, validated_data)


class StockAdjustmentSerializer(serializers.Serializer):
    """স্টক বাড়ানো, কমানো বা ড্যামেজ হিসেবে মার্ক করার জন্য ভ্যালিডেশন সিরিয়ালাইজার"""
    ADJUSTMENT_TYPES = [
        ('add', 'Add / Restock'),
        ('remove', 'Manual Deduction'),
        ('damage', 'Mark Damaged'),
        ('set', 'Cycle Count / Physical Audit'),
    ]

    quantity = serializers.IntegerField(min_value=1)
    adjustment_type = serializers.ChoiceField(choices=ADJUSTMENT_TYPES)
    notes = serializers.CharField(required=False, allow_blank=True)