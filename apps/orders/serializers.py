from rest_framework import serializers
from .models import Order, OrderItem, Cart, CartItem, Checkout, CheckoutLog

# ==========================================
# ORDER SERIALIZERS
# ==========================================
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'product_sku', 'quantity', 'unit_price', 'total_price', 'tax']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['order_number', 'status', 'created_at', 'updated_at']

# ==========================================
# CART SERIALIZERS
# ==========================================
class CartItemSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(source='get_total_price', max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'product_sku', 'quantity', 'unit_price', 'total_price']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = [
            'id','tenant', 'cart_token', 'status', 'subtotal', 'tax_total', 
            'shipping_total', 'discount_total', 'grand_total', 
            'coupon_code', 'items', 'created_at'
        ]
        read_only_fields = [
            'subtotal', 'tax_total', 'shipping_total', 
            'discount_total', 'grand_total'
        ]

# ==========================================
# CHECKOUT SERIALIZERS
# ==========================================
class CheckoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checkout
        fields = '__all__'
        read_only_fields = ['status', 'order', 'subtotal', 'tax_total', 'discount_total', 'grand_total', 'completed_at']