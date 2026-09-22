# apps/customers/views.py
from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core.cache import cache

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Customer
from .serializers import CustomerSerializer, UserRegistrationSerializer


class CustomerPingView(APIView):
    """Customer storefront ba dashboard-e active thakle real-time heartbeat update korbe"""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        user = request.user if request.user.is_authenticated else None
        if not email and user:
            email = getattr(user, 'email', None)

        if email:
            clean_email = email.strip().lower()
            now = timezone.now()
            # Cache-e 5 min-er jonno live active set kora
            cache.set(f"online_customer_{clean_email}", now, timeout=300)

            # Database-e updated_at timestamp sync kora
            Customer.objects.filter(
                Q(email__iexact=clean_email) | (Q(user=user) if user else Q())
            ).update(updated_at=now)

            return Response({'status': 'online', 'timestamp': now}, status=status.HTTP_200_OK)
        return Response({'error': 'Email required'}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        user = authenticate(username=email, password=password)
        
        if user:
            now = timezone.now()
            cache.set(f"online_customer_{email}", now, timeout=300)
            Customer.objects.filter(user=user).update(updated_at=now)

            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            })
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            current_tenant = getattr(request, 'tenant', None)
            phone_number = request.data.get('phone') or request.data.get('phone_number') or ''
            
            with transaction.atomic():
                user = serializer.save()
                if current_tenant and hasattr(user, 'tenant'):
                    user.tenant = current_tenant
                    user.save(update_fields=['tenant'])

                if current_tenant:
                    Customer.objects.update_or_create(
                        tenant=current_tenant,
                        email=user.email.strip().lower(),
                        defaults={
                            'user': user,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'phone': phone_number
                        }
                    )
            
            now = timezone.now()
            cache.set(f"online_customer_{user.email.strip().lower()}", now, timeout=300)

            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Registration successful, profile created.",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerViewSet(viewsets.ModelViewSet):
    """Merchant admin customer list, view ebong delete handler (Edit disallowed)"""
    serializer_class = CustomerSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ['get', 'delete', 'head', 'options']

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        qs = Customer.objects.select_related('user').all()
        if tenant:
            qs = qs.filter(tenant=tenant)
        return qs.order_by('-created_at')

    def destroy(self, request, *args, **kwargs):
        customer = self.get_object()
        linked_user = customer.user
        customer.delete()
        if linked_user and not linked_user.is_staff:
            linked_user.delete()
        return Response({'message': 'Customer deleted successfully.'}, status=status.HTTP_200_OK)