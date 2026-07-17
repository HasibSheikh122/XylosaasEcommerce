from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Order, Cart, CartItem, Checkout
from .serializers import OrderSerializer, CartSerializer, CartItemSerializer, CheckoutSerializer

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    lookup_field = 'cart_token' # ID এর বদলে token দিয়ে কার্ট খুঁজবে

    def perform_create(self, serializer):
        # request.data থেকে tenant আইডি বের করার চেষ্টা করুন
        tenant_id = self.request.data.get('tenant')
        
        # যদি tenant_id না থাকে, তবে একটি এরর দিন যেন আপনি বুঝতে পারেন সমস্যা কোথায়
        if not tenant_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"tenant": "This field is required."})
            
        serializer.save(tenant_id=tenant_id)

    @action(detail=True, methods=['post'])
    def add_item(self, request, cart_token=None):
        """কার্টে নতুন আইটেম যোগ করা বা পরিমাণ আপডেট করা"""
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        # প্রোডাক্ট এবং অন্যান্য লজিক ভ্যালিডেট করুন (এখানে ডেমো লজিক দেওয়া হলো)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_id=product_id,
            defaults={
                'product_name': request.data.get('product_name', 'Unknown'),
                'product_sku': request.data.get('product_sku', 'SKU-000'),
                'unit_price': request.data.get('unit_price', 0)
            }
        )

        if not created:
            cart_item.update_quantity(cart_item.quantity + quantity)
        else:
            cart.calculate_totals() # নতুন যোগ হলে টোটাল রিক্যালকুলেট হবে

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def apply_coupon(self, request, cart_token=None):
        """কার্টে কুপন অ্যাপ্লাই করা"""
        cart = self.get_object()
        coupon_code = request.data.get('coupon_code')
        
        success, message = cart.apply_coupon(coupon_code)
        if success:
            return Response({'message': message, 'cart': CartSerializer(cart).data}, status=status.HTTP_200_OK)
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
    

    @action(detail=True, methods=['post'])
    def remove_item(self, request, cart_token=None):
        """কার্ট থেকে নির্দিষ্ট আইটেম মুছে ফেলা"""
        cart = self.get_object()
        product_id = request.data.get('product_id')
        
        try:
            # কার্ট আইটেমটি খুঁজে বের করে ডিলিট করা
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
            cart_item.delete()
            
            # আইটেম ডিলিট করার পর টোটাল আবার হিসাব করা
            cart.calculate_totals()
            
            return Response(
                {'message': 'Item removed', 'cart': CartSerializer(cart).data}, 
                status=status.HTTP_200_OK
            )
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in cart'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class CheckoutViewSet(viewsets.ModelViewSet):
    queryset = Checkout.objects.all()
    serializer_class = CheckoutSerializer

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """চেকআউট প্রসেস শেষ করে অর্ডারে কনভার্ট করা"""
        checkout = self.get_object()
        
        if checkout.status == 'completed':
            return Response({'error': 'Checkout is already completed.'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            order = checkout.complete_checkout()
            return Response({
                'message': 'Order placed successfully!',
                'order_number': order.order_number
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """অর্ডার শুধুমাত্র দেখার জন্য (Create হবে Checkout থেকে)"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    lookup_field = 'order_number'