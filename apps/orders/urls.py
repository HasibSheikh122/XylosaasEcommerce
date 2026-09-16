from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, CheckoutViewSet, OrderViewSet

app_name = 'orders'

router = DefaultRouter()
router.register(r'carts', CartViewSet, basename='cart')
router.register(r'checkouts', CheckoutViewSet, basename='checkout')
router.register(r'', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
]