from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CarrierViewSet,
    ShippingZoneViewSet,
    ShippingMethodViewSet,
    ShippingRateViewSet,
    ShipmentViewSet,
)

router = DefaultRouter()
router.register(r'carriers', CarrierViewSet, basename='shipping-carrier')
router.register(r'zones', ShippingZoneViewSet, basename='shipping-zone')
router.register(r'methods', ShippingMethodViewSet, basename='shipping-method')
router.register(r'rates', ShippingRateViewSet, basename='shipping-rate')
router.register(r'shipments', ShipmentViewSet, basename='shipping-shipment')

urlpatterns = [
    path('', include(router.urls)),
]