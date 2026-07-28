from rest_framework import viewsets, permissions, status
from .models import Customer
from .serializers import CustomerSerializer, UserRegistrationSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


from rest_framework import serializers

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(username=email, password=password) # ইমেইল দিয়ে অথেনটিকেশন
        
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        print("--- Request received in RegisterView ---")
        print("Tenant:", getattr(request, 'tenant', 'No tenant found'))

        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            # এখানে current_tenant কে রিকোয়েস্ট থেকে নিতে হবে
            current_tenant = request.tenant 
            
            with transaction.atomic():
                user = serializer.save()
                
                # এখন current_tenant সঠিকভাবে কাজ করবে
                Customer.objects.create(
                    tenant=current_tenant, 
                    user=user,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
            
            return Response(
                {"message": "Registration successful, profile created."}, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # টেন্যান্ট অনুযায়ী ডেটা ফিল্টার করা
        return Customer.objects.filter(tenant=self.request.user.tenant)

    def perform_create(self, serializer):
        # নতুন কাস্টমার তৈরির সময় বর্তমান টেন্যান্ট সেট করা
        serializer.save(tenant=self.request.tenant)