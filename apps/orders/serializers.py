from rest_framework import serializers
from .models import Order, OrderItem, Cart, CartItem, Checkout, CheckoutLog


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'variant_data', 'quantity', 'unit_price', 'total_price', 'tax'
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'tenant', 'customer', 'order_number', 'status', 'status_display',
            'subtotal', 'tax', 'shipping_cost', 'discount', 'total',
            'shipping_address', 'billing_address', 'shipping_method',
            'tracking_number', 'shipped_at', 'delivered_at',
            'payment_method', 'payment_status', 'payment_id',
            'notes', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'order_number', 'status', 'created_at', 'updated_at']


class CartItemSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()
    tax_amount = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'variant_data', 'quantity', 'unit_price', 'tax_rate',
            'total_price', 'tax_amount', 'weight_per_unit'
        ]
        read_only_fields = ['id', 'product_name', 'product_sku', 'unit_price', 'total_price', 'tax_amount']

    def get_total_price(self, obj):
        return float(obj.get_total_price())

    def get_tax_amount(self, obj):
        return float(obj.get_tax_amount())


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id', 'cart_token', 'status', 'total_items',
            'subtotal', 'tax_total', 'shipping_total', 'discount_total', 'grand_total',
            'coupon_code', 'coupon_discount', 'shipping_method',
            'shipping_address', 'billing_address', 'notes',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'cart_token', 'status', 'total_items',
            'subtotal', 'tax_total', 'shipping_total', 'discount_total', 'grand_total',
            'coupon_discount', 'created_at', 'updated_at'
        ]

    def get_total_items(self, obj):
        return obj.get_total_items() if hasattr(obj, 'get_total_items') else obj.items.count()


class AddCartItemSerializer(serializers.Serializer):
    """সার্ভার-সাইড প্রাইস ও স্টক ভ্যালিডেশন ইনপুট"""
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(default=1, min_value=1)
    variant_data = serializers.DictField(default=dict, required=False)


class UpdateCartItemQuantitySerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)


class CheckoutSerializer(serializers.ModelSerializer):
    cart_token = serializers.CharField(write_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    grand_total = serializers.SerializerMethodField()

    class Meta:
        model = Checkout
        fields = [
            'id', 'cart_token', 'order', 'order_number', 'status',
            'payment_method', 'payment_status', 'payment_id',
            'shipping_address', 'billing_address', 'shipping_method', 'shipping_cost',
            'customer_email', 'customer_phone', 'customer_name', 'customer_notes',
            'grand_total', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'order', 'status', 'payment_status', 'shipping_cost', 'created_at', 'updated_at', 'completed_at']

    def get_grand_total(self, obj):
        return float(obj.cart.grand_total) if obj.cart else 0.0


class CheckoutLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckoutLog
        fields = ['id', 'checkout', 'log_type', 'message', 'data', 'created_at']
        read_only_fields = ['id', 'created_at']