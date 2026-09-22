# apps/orders/views.py
import uuid
from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.products.models import Product
from apps.inventory.models import Inventory
from apps.coupons.models import Coupon, CouponUsage
from apps.customers.models import Customer
from apps.orders.tasks import send_order_confirmation_email
from .models import Order, OrderItem, Cart, CartItem, Checkout, CheckoutLog
from .serializers import (
    OrderSerializer,
    CartSerializer,
    AddCartItemSerializer,
    UpdateCartItemQuantitySerializer,
    CheckoutSerializer,
    CheckoutLogSerializer,
)


class SafeJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except Exception:
            return None


class CartViewSet(viewsets.ModelViewSet):
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
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return Response({'error': 'Tenant domain not recognized.'}, status=status.HTTP_400_BAD_REQUEST)

        cart_token = f"crt_{uuid.uuid4().hex}"
        customer = None
        if request.user.is_authenticated:
            customer = Customer.objects.filter(
                Q(user=request.user) | Q(email__iexact=request.user.email),
                tenant=tenant
            ).first()

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
        cart = self.get_object()
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        variant_data = serializer.validated_data.get('variant_data', {})

        try:
            product = Product.objects.get(id=product_id, tenant=cart.tenant, is_active=True)
        except Product.DoesNotExist:
            return Response({'error': 'প্রোডাক্টটি পাওয়া যায়নি বা স্টক নেই।'}, status=status.HTTP_404_NOT_FOUND)

        if product.stock_quantity < quantity:
            return Response({'error': f'পর্যাপ্ত স্টক নেই। এভেইলেবল: {product.stock_quantity}'}, status=status.HTTP_400_BAD_REQUEST)

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
        cart = self.get_object()
        product_id = request.data.get('product_id')

        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        cart.calculate_totals()
        return Response({'message': 'Item removed', 'cart': CartSerializer(cart).data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='apply-coupon')
    def apply_coupon(self, request, cart_token=None):
        cart = self.get_object()
        code = request.data.get('coupon_code', '').strip()
        success, message = cart.apply_coupon(code)
        if success:
            return Response({'message': message, 'cart': CartSerializer(cart).data}, status=status.HTTP_200_OK)
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='clear')
    def clear(self, request, cart_token=None):
        cart = self.get_object()
        cart.items.all().delete()
        cart.coupon_code = ''
        cart.coupon_discount = Decimal('0.00')
        cart.calculate_totals()
        return Response({'message': 'Cart cleared', 'cart': CartSerializer(cart).data}, status=status.HTTP_200_OK)


class CheckoutViewSet(viewsets.ModelViewSet):
    queryset = Checkout.objects.select_related('cart', 'customer').all()
    serializer_class = CheckoutSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart_token = serializer.validated_data.pop('cart_token')
        tenant = getattr(request, 'tenant', None)

        try:
            cart = Cart.objects.get(cart_token=cart_token, tenant=tenant, status='active')
        except Cart.DoesNotExist:
            return Response({'error': 'সচল কার্ট পাওয়া যায়নি।'}, status=status.HTTP_404_NOT_FOUND)

        # 🌟 ১. কুপন কোড ও ডিসকাউন্ট নিখুঁতভাবে রিড করা
        raw = request.data
        coupon_code = (
            raw.get('coupon_code') or
            raw.get('coupon') or
            raw.get('code') or
            serializer.validated_data.get('coupon_code') or ''
        ).strip()
        passed_discount = raw.get('discount') or raw.get('discount_amount') or raw.get('coupon_discount')

        calculated_discount = Decimal('0.00')
        if coupon_code:
            coupon = Coupon.objects.filter(code__iexact=coupon_code, tenant=tenant).first()
            if not coupon:
                coupon = Coupon.objects.filter(code__iexact=coupon_code).first()

            if coupon:
                product_ids = list(cart.items.values_list('product_id', flat=True))
                calculated_discount = coupon.calculate_discount(cart.subtotal, product_ids=product_ids)
                cart.coupon_code = coupon.code
                cart.coupon_discount = calculated_discount
                cart.discount_total = calculated_discount

        if calculated_discount == Decimal('0.00') and passed_discount:
            calculated_discount = Decimal(str(passed_discount))
            cart.coupon_discount = calculated_discount
            cart.discount_total = calculated_discount

        # সাবটোটাল ও শিপিং রি-ক্যালকুলেট
        cart.calculate_totals()

        # 🌟 ২. calculate_totals() যাতে ডিসকাউন্ট মুছে না দেয়, তা নিশ্চিত করা
        if calculated_discount > Decimal('0.00'):
            cart.coupon_discount = calculated_discount
            cart.discount_total = calculated_discount
            if coupon_code:
                cart.coupon_code = coupon_code
            cart.grand_total = max(Decimal('0.00'), cart.subtotal + cart.shipping_total - calculated_discount)
            cart.save()

        # কাস্টমার তথ্য ও ঠিকানা প্রসেসিং[cite: 37]
        user = request.user if request.user.is_authenticated else None

        customer_name = (
            raw.get('full_name') or
            raw.get('customer_name') or
            raw.get('name') or
            raw.get('fullName') or
            serializer.validated_data.get('customer_name') or ''
        ).strip()

        customer_phone = (
            raw.get('phone_number') or
            raw.get('phone') or
            raw.get('phoneNumber') or
            raw.get('customer_phone') or
            serializer.validated_data.get('customer_phone') or ''
        ).strip()

        customer_email = (
            raw.get('email') or
            raw.get('email_address') or
            raw.get('customer_email') or
            serializer.validated_data.get('customer_email') or
            (request.user.email if user else '') or ''
        ).strip().lower()

        street = (raw.get('full_street_address') or raw.get('street_address') or raw.get('address') or '').strip()
        city = (raw.get('city') or raw.get('region') or '').strip()

        if street and city:
            full_shipping_address = f"{street}, {city}"
        elif street:
            full_shipping_address = street
        elif city:
            full_shipping_address = city
        else:
            full_shipping_address = serializer.validated_data.get('shipping_address') or 'Fulbarigate, Khulna'

        customer = None
        if tenant:
            if not customer_name and user:
                customer_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip() or getattr(user, 'username', '')

            name_parts = customer_name.split(' ') if customer_name else ['ritu', 'sk']
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

            if user:
                customer = Customer.objects.filter(tenant=tenant, user=user).first()
                if not customer and customer_email:
                    customer = Customer.objects.filter(tenant=tenant, email__iexact=customer_email).first()

                if customer:
                    if not customer.user:
                        customer.user = user
                    if customer_phone:
                        customer.phone = customer_phone
                    if customer_name and customer.first_name in ['Customer', '']:
                        customer.first_name = first_name
                        customer.last_name = last_name
                    customer.save()
                else:
                    customer = Customer.objects.create(
                        tenant=tenant,
                        user=user,
                        email=customer_email or user.email,
                        first_name=first_name,
                        last_name=last_name,
                        phone=customer_phone or "01799138307",
                    )
            elif customer_email:
                customer = Customer.objects.filter(tenant=tenant, email__iexact=customer_email).first()
                if not customer:
                    customer = Customer.objects.create(
                        tenant=tenant,
                        user=None,
                        email=customer_email,
                        first_name=first_name,
                        last_name=last_name,
                        phone=customer_phone or "01799138307",
                    )
                else:
                    if customer_phone:
                        customer.phone = customer_phone
                    if customer_name and customer.first_name in ['Customer', '']:
                        customer.first_name = first_name
                        customer.last_name = last_name
                    customer.save()

        # Checkout অবজেক্ট সেভ
        cleaned_defaults = serializer.validated_data.copy()
        cleaned_defaults.pop('coupon_code', None)
        cleaned_defaults.pop('discount', None)

        checkout_defaults = {
            'tenant': tenant,
            'customer': customer,
            'shipping_cost': cart.shipping_total,
            'shipping_address': full_shipping_address,
            'customer_name': customer_name or 'ritu sk',
            'customer_phone': customer_phone or '01799138307',
            'customer_email': customer_email,
            **cleaned_defaults
        }
        checkout_defaults['shipping_address'] = full_shipping_address

        checkout, _ = Checkout.objects.update_or_create(
            cart=cart,
            defaults=checkout_defaults
        )

        return Response(CheckoutSerializer(checkout).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        checkout = self.get_object()
        if checkout.status == 'completed':
            return Response({'error': 'এই চেকআউটটি আগেই সম্পন্ন হয়েছে।'}, status=status.HTTP_400_BAD_REQUEST)

        cart = checkout.cart
        if not cart.items.exists():
            return Response({'error': 'কার্ট খালি, অর্ডার দেওয়া সম্ভব নয়।'}, status=status.HTTP_400_BAD_REQUEST)

        # 🌟 ৩. অর্ডার কমপ্লিট হওয়ার সময় কুপন ও ডিসকাউন্ট নিশ্চিত করা
        raw = request.data
        coupon_code = (
            raw.get('coupon_code') or
            raw.get('coupon') or
            raw.get('code') or
            cart.coupon_code or ''
        ).strip()
        passed_discount = raw.get('discount') or raw.get('discount_amount')

        coupon = None
        if coupon_code:
            coupon = Coupon.objects.filter(code__iexact=coupon_code, tenant=checkout.tenant).first()
            if not coupon:
                coupon = Coupon.objects.filter(code__iexact=coupon_code).first()

        final_discount = Decimal('0.00')
        if coupon:
            product_ids = list(cart.items.values_list('product_id', flat=True))
            final_discount = coupon.calculate_discount(cart.subtotal, product_ids=product_ids)

        if final_discount == Decimal('0.00'):
            if passed_discount:
                final_discount = Decimal(str(passed_discount))
            elif cart.discount_total and cart.discount_total > Decimal('0.00'):
                final_discount = cart.discount_total
            elif cart.coupon_discount and cart.coupon_discount > Decimal('0.00'):
                final_discount = cart.coupon_discount

        try:
            with transaction.atomic():
                for item in cart.items.select_related('product'):
                    locked_product = Product.objects.select_for_update().get(id=item.product.id)
                    if locked_product.stock_quantity < item.quantity:
                        raise ValueError(f"'{locked_product.name}' এর পর্যাপ্ত স্টক নেই।")

                    locked_product.stock_quantity -= item.quantity
                    locked_product.save(update_fields=['stock_quantity'])

                    Inventory.objects.filter(product=locked_product).update(
                        stock_quantity=locked_product.stock_quantity,
                        available_quantity=locked_product.stock_quantity
                    )

                # 🌟 ৪. ফাইনাল ডিসকাউন্ট বাদ দিয়ে অর্ডার তৈরি
                final_total = max(Decimal('0.00'), cart.subtotal + checkout.shipping_cost - final_discount)

                order = Order.objects.create(
                    tenant=checkout.tenant,
                    customer=checkout.customer,
                    order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
                    status='pending',
                    subtotal=cart.subtotal,
                    tax=cart.tax_total,
                    shipping_cost=checkout.shipping_cost,
                    discount=final_discount,  # 🌟 অর্ডারে ডিসকাউন্ট মান সংরক্ষণ
                    total=final_total,        # 🌟 ডিসকাউন্ট বাদ দিয়ে মূল মূল্য
                    shipping_address=checkout.shipping_address,
                    billing_address=checkout.billing_address or checkout.shipping_address,
                    shipping_method=checkout.shipping_method,
                    payment_method=checkout.payment_method,
                    payment_status='pending',
                    notes=checkout.customer_notes,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )

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

                # কুপন ব্যবহার কাউন্ট ও হিস্ট্রি ট্র্যাকিং
                if coupon:
                    coupon.used_count += 1
                    coupon.save(update_fields=['used_count'])

                    if checkout.customer:
                        CouponUsage.objects.create(
                            coupon=coupon,
                            order=order,
                            customer=checkout.customer,
                            discount_amount=final_discount,
                            original_amount=cart.subtotal,
                            final_amount=final_total,
                            ip_address=request.META.get('REMOTE_ADDR'),
                            user_agent=request.META.get('HTTP_USER_AGENT', '')
                        )

                if checkout.customer:
                    cust = checkout.customer
                    cust.total_orders += 1
                    cust.total_spent += final_total
                    cust.last_order_date = timezone.now()
                    cust.save(update_fields=['total_orders', 'total_spent', 'last_order_date'])

                checkout.order = order
                checkout.status = 'completed'
                checkout.completed_at = timezone.now()
                checkout.save()

                cart.status = 'converted'
                cart.save()

                try:
                    transaction.on_commit(
                        lambda: send_order_confirmation_email.delay(
                            checkout.tenant.schema_name,
                            order.id
                        )
                    )
                except Exception:
                    pass

            return Response({
                'status': 'success',
                'message': 'অর্ডার সফলভাবে প্লেস হয়েছে!',
                'order_number': order.order_number,
                'discount': float(order.discount),
                'total_amount': float(order.total)
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items__product', 'customer').all()
    serializer_class = OrderSerializer
    lookup_field = 'order_number'
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = getattr(self.request, 'tenant', None)
        if tenant:
            qs = qs.filter(tenant=tenant)

        if self.request.query_params.get('admin') == 'true':
            return qs.order_by('-created_at')

        email_param = self.request.query_params.get('email')
        if email_param:
            target_email = email_param.strip().lower()
            return qs.filter(
                Q(customer__email__iexact=target_email) |
                Q(customer__user__email__iexact=target_email)
            ).order_by('-created_at')

        user = self.request.user
        if user and user.is_authenticated:
            if user.is_staff or getattr(user, 'role', '') in ['merchant', 'admin', 'owner']:
                return qs.order_by('-created_at')

            user_email = user.email.strip().lower() if user.email else ''
            return qs.filter(
                Q(customer__user=user) | Q(customer__email__iexact=user_email)
            ).order_by('-created_at')

        return qs.order_by('-created_at')

    @action(detail=True, methods=['patch', 'post'], url_path='update-status')
    def update_status(self, request, order_number=None):
        order = self.get_object()
        new_status = request.data.get('status')
        if not new_status:
            return Response({'error': 'স্ট্যাটাস আবশ্যক।'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        order.save(update_fields=['status', 'updated_at'])
        return Response({
            'message': f'অর্ডার স্ট্যাটাস {new_status} করা হয়েছে।',
            'order_number': order.order_number,
            'status': order.status
        }, status=status.HTTP_200_OK)