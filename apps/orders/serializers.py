# apps/orders/serializers.py
from decimal import Decimal
from rest_framework import serializers
from .models import Order, OrderItem, Cart, CartItem, Checkout, CheckoutLog
from apps.customers.models import Customer


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'variant_data', 'quantity', 'unit_price', 'total_price', 'tax'
        ]


class CustomerMiniSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'full_name', 'email', 'phone']

    def get_full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name and name.lower() != 'customer' else "ritu sk"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    customer_data = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    full_address = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'tenant', 'customer', 'customer_data', 'order_number', 'status', 'status_display',
            'subtotal', 'tax', 'shipping_cost', 'discount', 'total',
            'shipping_address', 'full_address', 'billing_address', 'shipping_method',
            'tracking_number', 'shipped_at', 'delivered_at',
            'payment_method', 'payment_status', 'payment_id',
            'notes', 'items', 'created_at', 'updated_at',
            'customer_name', 'customer_phone', 'customer_email'
        ]
        read_only_fields = ['id', 'tenant', 'order_number', 'status', 'created_at', 'updated_at']

    def get_customer_data(self, obj):
        if obj.customer:
            return CustomerMiniSerializer(obj.customer).data
        return None

    def get_customer_name(self, obj):
        if obj.customer:
            name = f"{obj.customer.first_name} {obj.customer.last_name}".strip()
            if name and name.lower() != 'customer':
                return name
            if obj.customer.user:
                u = obj.customer.user
                u_name = f"{getattr(u, 'first_name', '')} {getattr(u, 'last_name', '')}".strip()
                if u_name:
                    return u_name
                if getattr(u, 'username', ''):
                    return u.username
            if obj.customer.email:
                return obj.customer.email.split('@')[0]
        return "ritu sk"

    def get_customer_phone(self, obj):
        if obj.customer and obj.customer.phone and obj.customer.phone != "N/A":
            return obj.customer.phone
        if obj.customer and obj.customer.user:
            u_phone = getattr(obj.customer.user, 'phone', None)
            if u_phone:
                return u_phone
        return "01799138307"

    def get_customer_email(self, obj):
        if obj.customer and obj.customer.email:
            return obj.customer.email
        if obj.customer and obj.customer.user:
            return getattr(obj.customer.user, 'email', '')
        return "ritu@gmail.com"

    def get_full_address(self, obj):
        addr = obj.shipping_address or ""
        if isinstance(addr, dict):
            street = addr.get('street_address', '')
            city = addr.get('city', '')
            return f"{street}, {city}".strip(', ')
        addr_str = str(addr).strip()
        if addr_str == "Khulna" or not addr_str:
            return "Fulbarigate, Khulna"
        return addr_str


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

    # কাস্টমার ও ডেলিভারি তথ্য
    full_name = serializers.CharField(write_only=True, required=False)
    phone_number = serializers.CharField(write_only=True, required=False)
    phone = serializers.CharField(write_only=True, required=False)
    email = serializers.CharField(write_only=True, required=False)
    street_address = serializers.CharField(write_only=True, required=False)
    city = serializers.CharField(write_only=True, required=False)

    # 🌟 কুপন ও ডিসকাউন্ট প্যারামিটার পারমিট করা
    coupon_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    discount = serializers.DecimalField(write_only=True, required=False, max_digits=10, decimal_places=2)

    class Meta:
        model = Checkout
        fields = [
            'id', 'cart_token', 'order', 'order_number', 'status',
            'payment_method', 'payment_status', 'payment_id',
            'shipping_address', 'billing_address', 'shipping_method', 'shipping_cost',
            'customer_email', 'customer_phone', 'customer_name', 'customer_notes',
            'grand_total', 'created_at', 'updated_at', 'completed_at',
            'full_name', 'phone_number', 'phone', 'email', 'street_address', 'city',
            'coupon_code', 'discount'
        ]
        read_only_fields = ['id', 'order', 'status', 'payment_status', 'shipping_cost', 'created_at', 'updated_at', 'completed_at']

    def get_grand_total(self, obj):
        return float(obj.cart.grand_total) if obj.cart else 0.0


class CheckoutLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckoutLog
        fields = ['id', 'checkout', 'log_type', 'message', 'data', 'created_at']
        read_only_fields = ['id', 'created_at']