from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from apps.customers.models import Customer
from .serializers import (
    UserSerializer,
    UserRegisterSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    MerchantTokenObtainPairSerializer,
)

User = get_user_model()


class SafeJWTAuthentication(JWTAuthentication):
    """টোকেন মেয়াদ শেষ হলেও ৪০১ দিয়ে রিকোয়েস্ট ব্লক না করে সেফলি পাস করায়"""
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except Exception:
            return None


class CustomTokenObtainPairView(TokenObtainPairView):
    """সাধারণ গ্রাহক লগইন ভিউ"""
    serializer_class = CustomTokenObtainPairSerializer


class MerchantTokenObtainPairView(TokenObtainPairView):
    """মার্চেন্ট ও স্টোর ওনারদের জন্য পৃথক লগইন ভিউ"""
    serializer_class = MerchantTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related('tenant').all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'phone']

    def get_permissions(self):
        if self.action == 'register':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        if not user.is_superuser:
            if hasattr(self.request, 'tenant') and self.request.tenant:
                qs = qs.filter(tenant=self.request.tenant)
            elif getattr(user, 'tenant', None):
                qs = qs.filter(tenant=user.tenant)
            else:
                qs = qs.filter(id=user.id)
        return qs

    @action(detail=False, methods=['POST'], url_path='register')
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "status": "success",
            "message": "রেজিস্ট্রেশন সফলভাবে সম্পন্ন হয়েছে!",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": getattr(user, 'role', 'customer')
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['GET', 'PUT', 'PATCH'], url_path='me')
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserProfileView(APIView):
    """গ্রাহক প্রোফাইল আপডেট API"""
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user = request.user if (request.user and request.user.is_authenticated) else None
        if not user:
            email = request.query_params.get('email', '').strip().lower()
            if email:
                user = User.objects.filter(email__iexact=email).first()

        if not user:
            return Response({'error': 'ব্যবহারকারী সনাক্ত করা যায়নি।'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': getattr(user, 'phone', ''),
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        user = request.user if (request.user and request.user.is_authenticated) else None
        if not user:
            email = request.data.get('email', '').strip().lower()
            if email:
                user = User.objects.filter(email__iexact=email).first()

        if not user:
            return Response({'error': 'ব্যবহারকারী সনাক্ত করা যায়নি। অনুগ্রহ করে পুনরায় লগইন করুন।'}, status=status.HTTP_400_BAD_REQUEST)

        first_name = request.data.get('first_name', user.first_name).strip()
        last_name = request.data.get('last_name', user.last_name).strip()
        phone = request.data.get('phone', getattr(user, 'phone', '')).strip()

        user.first_name = first_name
        user.last_name = last_name
        if hasattr(user, 'phone'):
            user.phone = phone
        user.save()

        tenant = getattr(request, 'tenant', None)
        customer_qs = Customer.objects.filter(Q(user=user) | Q(email__iexact=user.email))
        if tenant:
            customer_qs = customer_qs.filter(tenant=tenant)

        customer_qs.update(
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )

        return Response({
            'message': 'প্রোফাইল তথ্য সফলভাবে আপডেট হয়েছে!',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': phone,
            }
        }, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """পাসওয়ার্ড পরিবর্তন API"""
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = request.user if (request.user and request.user.is_authenticated) else None
        if not user:
            email = request.data.get('email', '').strip().lower()
            if email:
                user = User.objects.filter(email__iexact=email).first()

        if not user:
            return Response({'error': 'ব্যবহারকারী সনাক্ত করা যায়নি।'}, status=status.HTTP_400_BAD_REQUEST)

        old_password = request.data.get('old_password', '')
        new_password = request.data.get('new_password', '')

        if not old_password or not new_password:
            return Response({'error': 'বর্তমান ও নতুন উভয় পাসওয়ার্ড দেওয়া আবশ্যক।'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({'error': 'বর্তমান পাসওয়ার্ডটি সঠিক নয়।'}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 6:
            return Response({'error': 'নতুন পাসওয়ার্ড ন্যূনতম ৬ অক্ষরের হতে হবে।'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({'message': 'পাসওয়ার্ড সফলভাবে পরিবর্তিত হয়েছে!'}, status=status.HTTP_200_OK)