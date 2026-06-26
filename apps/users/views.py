from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserRegisterSerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """রেজিস্ট্রেশনের জন্য অনুমতি উন্মুক্ত রাখা, বাকি সব কাজের জন্য লগইন বাধ্যতামূলক করা"""
        if self.action == 'register':
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['POST'], url_path='register')
    def register(self, request):
        """নতুন কাস্টমার সাইন-আপ এন্ডপয়েন্ট"""
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET', 'PUT', 'PATCH'], url_path='me')
    def me(self, request):
        """লগইন থাকা ইউজারের নিজের প্রোফাইল দেখা এবং আপডেট করার এন্ডপয়েন্ট"""
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        
        # প্রোফাইল আপডেট (PUT/PATCH) করার জন্য
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)