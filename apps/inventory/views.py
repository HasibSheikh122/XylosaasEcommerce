from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Inventory
from .serializers import InventorySerializer, StockAdjustmentSerializer


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.select_related('product', 'tenant').all()
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['warehouse_location', 'product']
    search_fields = ['product__name', 'warehouse_location', 'shelf_location', 'bin_number']
    ordering_fields = ['stock_quantity', 'available_quantity', 'updated_at']
    ordering = ['-updated_at']

    def get_queryset(self):
        qs = super().get_queryset()
        # Tenant Isolation: রিকোয়েস্টে টেন্যান্ট থাকলে শুধুমাত্র ওই টেন্যান্টের স্টক ফিল্টার হবে
        if hasattr(self.request, 'tenant'):
            qs = qs.filter(tenant=self.request.tenant)
        return qs

    def perform_create(self, serializer):
        kwargs = {}
        if hasattr(self.request, 'tenant'):
            kwargs['tenant'] = self.request.tenant
        serializer.save(**kwargs)

    @action(detail=True, methods=['post'], url_path='adjust-stock')
    def adjust_stock(self, request, pk=None):
        """
        Transactional Stock Adjustment:
        কোর ই-কমার্সে স্টক ইন/আউট করার সময় ডাটাবেজ লক (select_for_update) নিশ্চিত করে
        যাতে একই সাথে একাধিক রিকোয়েস্টে স্টক নেগেটিভ না হতে পারে।
        """
        inventory = self.get_object()
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        qty = serializer.validated_data['quantity']
        adj_type = serializer.validated_data['adjustment_type']

        with transaction.atomic():
            # Concurrency safe row-locking
            inventory = Inventory.objects.select_for_update().get(pk=inventory.pk)

            if adj_type == 'add':
                inventory.stock_quantity += qty
                inventory.last_restock_date = timezone.now()
            elif adj_type == 'remove':
                if inventory.available_quantity < qty:
                    return Response(
                        {'error': f'পর্যাপ্ত স্টক নেই। এভেইলেবল স্টক: {inventory.available_quantity}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                inventory.stock_quantity = max(0, inventory.stock_quantity - qty)
            elif adj_type == 'damage':
                if inventory.available_quantity < qty:
                    return Response(
                        {'error': f'ড্যামেজ মার্ক করার জন্য পর্যাপ্ত স্টক নেই। এভেইলেবল: {inventory.available_quantity}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                inventory.stock_quantity = max(0, inventory.stock_quantity - qty)
                inventory.damaged_quantity += qty
            elif adj_type == 'set':
                inventory.stock_quantity = qty

            # এভেইলেবল স্টক সিঙ্ক
            inventory.available_quantity = max(0, inventory.stock_quantity - inventory.reserved_quantity)
            inventory.save()

        return Response(
            InventorySerializer(inventory).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='low-stock')
    def low_stock(self, request):
        """যেসব প্রোডাক্টের স্টক থ্রেশহোল্ডের নিচে নেমে গেছে তাদের লিস্ট"""
        qs = self.get_queryset().filter(available_quantity__lte=F('low_stock_threshold'))
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)