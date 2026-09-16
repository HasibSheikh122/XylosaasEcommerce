from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from .serializers import (
    UserSerializer,
    UserRegisterSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """ইমেইল ও পাসওয়ার্ড দিয়ে JWT লগইন ভিউ"""
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    """ইউজার ম্যানেজমেন্ট ও প্রোফাইল কন্ট্রোলার"""
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
        
        # সুপার অ্যাডমিন ছাড়া বাকিদের নিজস্ব টেন্যান্টের ইউজার লিস্টে সীমাবদ্ধ রাখা
        if not user.is_superuser:
            if hasattr(self.request, 'tenant') and self.request.tenant:
                qs = qs.filter(tenant=self.request.tenant)
            elif user.tenant:
                qs = qs.filter(tenant=user.tenant)
            else:
                qs = qs.filter(id=user.id)
        return qs

    @action(detail=False, methods=['POST'], url_path='register')
    def register(self, request):
        """নতুন মার্চেন্ট বা কাস্টমার রেজিস্ট্রেশন এন্ডপয়েন্ট"""
        serializer = UserRegisterSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "status": "success",
            "message": "রেজিস্ট্রেশন সফলভাবে সম্পন্ন হয়েছে!",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['GET', 'PUT', 'PATCH'], url_path='me')
    def me(self, request):
        """লগইন থাকা ইউজারের নিজের প্রোফাইল দেখা এবং আপডেট করা"""
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['POST'], url_path='change-password')
    def change_password(self, request):
        """লগইন থাকা ইউজারের পাসওয়ার্ড পরিবর্তনের এন্ডপয়েন্ট"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({"status": "success", "message": "পাসওয়ার্ড সফলভাবে পরিবর্তন করা হয়েছে।"}, status=status.HTTP_200_OK)