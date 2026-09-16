import uuid
from decimal import Decimal
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Carrier, ShippingZone, ShippingMethod, ShippingRate, Shipment
from .serializers import (
    CarrierSerializer,
    ShippingZoneSerializer,
    ShippingMethodSerializer,
    ShippingRateSerializer,
    ShipmentSerializer,
    CalculateShippingSerializer,
    TrackingUpdateSerializer,
)


class BaseTenantViewSet(viewsets.ModelViewSet):
    """টেন্যান্ট অনুযায়ী কুয়েরিসেট ফিল্টার এবং অটো-অ্যাসাইন করার বেস ক্লাস"""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, 'tenant'):
            qs = qs.filter(tenant=self.request.tenant)
        return qs

    def perform_create(self, serializer):
        kwargs = {}
        if hasattr(self.request, 'tenant'):
            kwargs['tenant'] = self.request.tenant
        serializer.save(**kwargs)


class CarrierViewSet(BaseTenantViewSet):
    """কুরিয়ার সার্ভিস কনফিগারেশন ভিউসেট"""
    queryset = Carrier.objects.all()
    serializer_class = CarrierSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['carrier_type', 'is_active']
    search_fields = ['name']


class ShippingZoneViewSet(BaseTenantViewSet):
    """ডেলিভারি জোন ভিউসেট"""
    queryset = ShippingZone.objects.all()
    serializer_class = ShippingZoneSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'is_default']
    search_fields = ['name']
    ordering_fields = ['priority', 'name']


class ShippingMethodViewSet(BaseTenantViewSet):
    """শিপিং মেথড এবং চার্জ ক্যালকুলেশন ভিউসেট"""
    queryset = ShippingMethod.objects.select_related('carrier').prefetch_related('zones').all()
    serializer_class = ShippingMethodSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['method_type', 'is_active', 'is_available_for_cod']
    search_fields = ['name', 'carrier__name']
    ordering_fields = ['priority', 'base_cost', 'name']

    @action(detail=False, methods=['post'], url_path='calculate-rates')
    def calculate_rates(self, request):
        serializer = CalculateShippingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        weight_kg = serializer.validated_data['weight_kg']
        item_count = serializer.validated_data['item_count']
        subtotal = serializer.validated_data['subtotal']
        address = serializer.validated_data.get('address', {})

        methods = self.get_queryset().filter(is_active=True)
        available_rates = []

        for method in methods:
            if method.zones.exists() and address:
                matched_zone = any(zone.is_in_zone(address) for zone in method.zones.all())
                if not matched_zone:
                    continue

            cost = method.calculate_cost(weight_kg, item_count, subtotal, address)
            if cost is not None:
                available_rates.append({
                    'method_id': method.id,
                    'method_name': method.name,
                    'method_type': method.method_type,
                    'delivery_days': f"{method.delivery_days_min}-{method.delivery_days_max} days",
                    'shipping_cost': float(cost),
                    'is_cod_available': method.is_available_for_cod,
                })

        return Response({'available_methods': available_rates}, status=status.HTTP_200_OK)


class ShippingRateViewSet(BaseTenantViewSet):
    """কন্ডিশনাল শিপিং রেট ভিউসেট"""
    queryset = ShippingRate.objects.select_related('method', 'zone').all()
    serializer_class = ShippingRateSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['method', 'zone', 'is_active']
    ordering_fields = ['priority', 'rate']


class ShipmentViewSet(BaseTenantViewSet):
    """অর্ডার শিপমেন্ট ট্র্যাকিং ভিউসেট"""
    queryset = Shipment.objects.select_related('order', 'method', 'tenant').all()
    serializer_class = ShipmentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'carrier_name', 'order']
    search_fields = ['shipment_number', 'tracking_number', 'carrier_name']
    ordering_fields = ['created_at', 'expected_delivery_date']

    def perform_create(self, serializer):
        kwargs = {}
        if hasattr(self.request, 'tenant'):
            kwargs['tenant'] = self.request.tenant
        if 'shipment_number' not in serializer.validated_data:
            kwargs['shipment_number'] = f"SHP-{uuid.uuid4().hex[:8].upper()}"
        serializer.save(**kwargs)

    @action(detail=True, methods=['post'], url_path='update-tracking')
    def update_tracking(self, request, pk=None):
        shipment = self.get_object()
        serializer = TrackingUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        status_val = serializer.validated_data['status']
        desc = serializer.validated_data['description']
        loc = serializer.validated_data.get('location', '')

        shipment.add_tracking_update(status=status_val, description=desc, location=loc)
        return Response(
            {'message': 'ট্র্যাকিং আপডেট হয়েছে', 'shipment': ShipmentSerializer(shipment).data},
            status=status.HTTP_200_OK
        )