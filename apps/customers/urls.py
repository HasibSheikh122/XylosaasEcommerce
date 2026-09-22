# apps/customers/urls.py
from django.urls import path
from .views import CustomerViewSet, RegisterView, LoginView, CustomerPingView

urlpatterns = [
    path('login/', LoginView.as_view(), name='customer-login'),
    path('register/', RegisterView.as_view(), name='customer-register'),
    path('ping/', CustomerPingView.as_view(), name='customer-ping'),

    path('', CustomerViewSet.as_view({
        'get': 'list'
    }), name='customer-list'),

    path('<int:pk>/', CustomerViewSet.as_view({
        'get': 'retrieve',
        'delete': 'destroy'
    }), name='customer-detail'),
]