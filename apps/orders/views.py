import uuid
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.products.models import Product
from apps.inventory.models import Inventory
from apps.coupons.models import Coupon, CouponUsage
from apps.customers.models import Customer
from .models import Order, OrderItem, Cart, CartItem, Checkout, CheckoutLog
from .serializers import (
    OrderSerializer,
    CartSerializer,
    AddCartItemSerializer,
    UpdateCartItemQuantitySerializer,
    CheckoutSerializer,
    CheckoutLogSerializer,
)


class CartViewSet(viewsets.ModelViewSet):
    """শপিং কার্ট হ্যান্ডলার (গেস্ট ও লগইন করা ইউজার সবার জন্য উন্মুক্ত)"""
    queryset = Cart.objects.prefetch_related('items__product').all()
    serializer_class = CartSerializer
    lookup_field = 'cart_token'
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, 'tenant') and self.request.tenant:
            qs = qs.filter(tenant=self.request.tenant)
        return qs

    def create(self, request, *args, **kwargs):
        """নতুন কার্ট সেশন ইনিশিয়ালাইজ করা"""
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return Response({'error': 'Tenant domain not recognized.'}, status=status.HTTP_400_BAD_REQUEST)

        cart_token = f"crt_{uuid.uuid4().hex}"
        customer = None
        if request.user.is_authenticated:
            customer = Customer.objects.filter(user=request.user, tenant=tenant).first()

        cart = Cart.objects.create(
            tenant=tenant,
            cart_token=cart_token,
            customer=customer,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='add-item')
    def add_item(self, request, cart_token=None):
        """ডাটাবেজ থেকে দাম ও স্টক নিশ্চিত করে আইটেম যোগ করা"""
        cart = self.get_object()
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        variant_data = serializer.validated_data.get('variant_data', {})

        try:
            product = Product.objects.get(id=product_id, tenant=cart.tenant, is_active=True)
        except Product.DoesNotExist:
            return Response({'error': 'প্রোডাক্টটি পাওয়া যায়নি বা স্টক আউট।'}, status=status.HTTP_404_NOT_FOUND)

        if product.stock_quantity < quantity:
            return Response({'error': f'পর্যাপ্ত স্টক নেই। এভেইলেবল স্টক: {product.stock_quantity}'}, status=status.HTTP_400_BAD_REQUEST)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                'product_name': product.name,
                'product_sku': product.sku,
                'unit_price': product.price,
                'quantity': quantity,
                'variant_data': variant_data,
                'weight_per_unit': product.weight or Decimal('0.00'),
            }
        )

        if not created:
            new_qty = cart_item.quantity + quantity
            if product.stock_quantity < new_qty:
                return Response({'error': f'পর্যাপ্ত স্টক নেই। সর্বোচ্চ যোগ করা যাবে: {product.stock_quantity}'}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = new_qty
            cart_item.save()

        cart.calculate_totals()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='update-quantity')
    def update_quantity(self, request, cart_token=None):
        """কার্টে থাকা আইটেমের পরিমাণ পরিবর্তন করা"""
        cart = self.get_object()
        serializer = UpdateCartItemQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']

        try:
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
        except CartItem.DoesNotExist:
            return Response({'error': 'আইটেমটি কার্টে পাওয়া যায়নি।'}, status=status.HTTP_404_NOT_FOUND)

        if cart_item.product.stock_quantity < quantity:
            return Response({'error': f'পর্যাপ্ত স্টক নেই। এভেইলেবল: {cart_item.product.stock_quantity}'}, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = quantity
        cart_item.save()
        cart.calculate_totals()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='remove-item')
    def remove_item(self, request, cart_token=None):
        """কার্ট থেকে নির্দিষ্ট আইটেম মুছে ফেলা"""
        cart = self.get_object()
        product_id = request.data.get('product_id')

        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        cart.calculate_totals()
        return Response({'message': 'Item removed', 'cart': CartSerializer(cart).data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='apply-coupon')
    def apply_coupon(self, request, cart_token=None):
        """কার্টে কুপন কোড প্রয়োগ করা"""
        cart = self.get_object()
        code = request.data.get('coupon_code', '').strip()
        success, message = cart.apply_coupon(code)
        if success:
            return Response({'message': message, 'cart': CartSerializer(cart).data}, status=status.HTTP_200_OK)
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='clear')
    def clear(self, request, cart_token=None):
        """কার্ট সম্পূর্ণ খালি করা"""
        cart = self.get_object()
        cart.items.all().delete()
        cart.coupon_code = ''
        cart.coupon_discount = Decimal('0.00')
        cart.calculate_totals()
        return Response({'message': 'Cart cleared', 'cart': CartSerializer(cart).data}, status=status.HTTP_200_OK)


class CheckoutViewSet(viewsets.ModelViewSet):
    """চেকআউট সেশন তৈরি ও ডাটাবেজ রো-লকিং সহ অর্ডার ফাইনাল করার ভিউ"""
    queryset = Checkout.objects.select_related('cart', 'customer').all()
    serializer_class = CheckoutSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, 'tenant') and self.request.tenant:
            qs = qs.filter(tenant=self.request.tenant)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart_token = serializer.validated_data.pop('cart_token')
        tenant = getattr(request, 'tenant', None)

        try:
            cart = Cart.objects.get(cart_token=cart_token, tenant=tenant, status='active')
        except Cart.DoesNotExist:
            return Response({'error': 'সচল কার্ট পাওয়া যায়নি।'}, status=status.HTTP_404_NOT_FOUND)

        if not cart.items.exists():
            return Response({'error': 'কার্ট সম্পূর্ণ খালি।'}, status=status.HTTP_400_BAD_REQUEST)

        cart.calculate_totals()

        customer = None
        if request.user.is_authenticated:
            customer = Customer.objects.filter(user=request.user, tenant=tenant).first()

        checkout, _ = Checkout.objects.update_or_create(
            cart=cart,
            defaults={
                'tenant': tenant,
                'customer': customer,
                'shipping_cost': cart.shipping_total,
                **serializer.validated_data
            }
        )

        CheckoutLog.objects.create(
            checkout=checkout,
            log_type='step',
            message='Checkout initialized/updated'
        )

        return Response(CheckoutSerializer(checkout).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """
        🔒 ট্রানজাকশনাল ও অ্যাটমিক অর্ডার কমপ্লিশন:
        - কনকারেন্ট পারচেজ ঠেকাতে select_for_update() দিয়ে প্রোডাক্ট রো-লক
        - স্টক ডিডাকশন ও ইনভেন্টরি লেজার আপডেট
        - অর্ডার ও আইটেম স্ন্যাপশট তৈরি
        - কুপন ইউসেজ হিস্ট্রি সংরক্ষণ
        - কাস্টমার টোটাল স্পেন্ড ও লাস্ট অর্ডার ডেট আপডেট
        """
        checkout = self.get_object()
        if checkout.status == 'completed':
            return Response({'error': 'এই চেকআউটটি আগেই সম্পন্ন হয়েছে।'}, status=status.HTTP_400_BAD_REQUEST)

        cart = checkout.cart
        if not cart.items.exists():
            return Response({'error': 'কার্ট খালি, অর্ডার দেওয়া সম্ভব নয়।'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # ১. স্টক রো-লক ও রিডিউস
                for item in cart.items.select_related('product'):
                    locked_product = Product.objects.select_for_update().get(id=item.product.id)
                    if locked_product.stock_quantity < item.quantity:
                        raise ValueError(f"'{locked_product.name}' এর জন্য পর্যাপ্ত স্টক নেই। এভেইলেবল: {locked_product.stock_quantity}")

                    locked_product.stock_quantity -= item.quantity
                    locked_product.save(update_fields=['stock_quantity'])

                    # ইনভেন্টরি মডেল সিঙ্ক
                    Inventory.objects.filter(product=locked_product).update(
                        stock_quantity=locked_product.stock_quantity,
                        available_quantity=locked_product.stock_quantity
                    )

                # ২. অর্ডার তৈরি
                order = Order.objects.create(
                    tenant=checkout.tenant,
                    customer=checkout.customer,
                    order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
                    status='pending',
                    subtotal=cart.subtotal,
                    tax=cart.tax_total,
                    shipping_cost=checkout.shipping_cost,
                    discount=cart.discount_total,
                    total=cart.grand_total,
                    shipping_address=checkout.shipping_address,
                    billing_address=checkout.billing_address,
                    shipping_method=checkout.shipping_method,
                    payment_method=checkout.payment_method,
                    payment_status='pending',
                    notes=checkout.customer_notes,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )

                # ৩. অর্ডার আইটেম স্ন্যাপশট
                for item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        product_name=item.product_name,
                        product_sku=item.product_sku,
                        variant_data=item.variant_data,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total_price=item.get_total_price(),
                        tax=item.get_tax_amount(),
                    )

                # ৪. কুপন ব্যবহার হিস্ট্রি
                if cart.coupon_code:
                    try:
                        coupon = Coupon.objects.select_for_update().get(code=cart.coupon_code, tenant=checkout.tenant)
                        coupon.used_count += 1
                        coupon.save(update_fields=['used_count'])

                        if checkout.customer:
                            CouponUsage.objects.create(
                                coupon=coupon,
                                order=order,
                                customer=checkout.customer,
                                discount_amount=cart.discount_total,
                                original_amount=cart.subtotal,
                                final_amount=cart.grand_total,
                                ip_address=request.META.get('REMOTE_ADDR'),
                                user_agent=request.META.get('HTTP_USER_AGENT', '')
                            )
                    except Coupon.DoesNotExist:
                        pass

                # ৫. কাস্টমার মেট্রিক্স আপডেট
                if checkout.customer:
                    cust = checkout.customer
                    cust.total_orders += 1
                    cust.total_spent += cart.grand_total
                    cust.last_order_date = timezone.now()
                    cust.save(update_fields=['total_orders', 'total_spent', 'last_order_date'])

                # ৬. চেকআউট ও কার্ট সমাপ্ত করা
                checkout.order = order
                checkout.status = 'completed'
                checkout.completed_at = timezone.now()
                checkout.save()

                cart.status = 'converted'
                cart.save()

                CheckoutLog.objects.create(
                    checkout=checkout,
                    log_type='success',
                    message=f'Order {order.order_number} successfully placed.'
                )

            return Response({
                'status': 'success',
                'message': 'অর্ডারটি সফলভাবে প্লেস করা হয়েছে!',
                'order_number': order.order_number,
                'total_amount': float(order.total)
            }, status=status.HTTP_201_CREATED)

        except ValueError as val_err:
            CheckoutLog.objects.create(checkout=checkout, log_type='error', message=str(val_err))
            return Response({'error': str(val_err)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            CheckoutLog.objects.create(checkout=checkout, log_type='error', message=str(e))
            return Response({'error': f'অর্ডার প্রক্রিয়াকরণে সমস্যা হয়েছে: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """অর্ডার হিস্ট্রি ও ট্র্যাকিং ভিউ"""
    queryset = Order.objects.prefetch_related('items').all()
    serializer_class = OrderSerializer
    lookup_field = 'order_number'
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if hasattr(self.request, 'tenant') and self.request.tenant:
            qs = qs.filter(tenant=self.request.tenant)

        # সাধারণ কাস্টমার কেবল তার নিজস্ব অর্ডারগুলো দেখতে পারবে
        if not user.is_staff:
            customer = Customer.objects.filter(user=user).first()
            if customer:
                qs = qs.filter(customer=customer)
            else:
                qs = qs.none()

        return qs