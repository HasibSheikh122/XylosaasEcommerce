# apps/chat/views.py
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from .models import ChatRoom, ChatMessage
from .serializers import ChatRoomSerializer, ChatMessageSerializer

User = get_user_model()


class ChatRoomListView(generics.ListAPIView):
    """মার্চেন্ট এবং কাস্টমারদের সংশ্লিষ্ট চ্যাটরুমের তালিকা প্রদান"""
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        tenant = getattr(self.request, 'tenant', None)

        is_admin = user.is_staff or user.is_superuser or getattr(user, 'role', '') in ['merchant', 'owner', 'admin']
        if is_admin:
            qs = ChatRoom.objects.all()
        else:
            qs = ChatRoom.objects.filter(customer=user)

        if tenant:
            qs = qs.filter(tenant=tenant)
        return qs.order_by('-updated_at')


class ChatRoomCreateView(APIView):
    """নতুন চ্যাটরুম তৈরি এবং স্বয়ংক্রিয় এআই ওয়েলকাম মেসেজ প্রেরণ"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # ১. টেন্যান্ট নির্ণয়
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            host = request.get_host()
            subdomain = host.split('.')[0] if '.' in host else 'nextlook'
            try:
                from apps.tenants.models import Tenant
                tenant = Tenant.objects.filter(subdomain__iexact=subdomain).first() or Tenant.objects.first()
            except Exception:
                tenant = None

        if not tenant:
            return Response({"error": "Store/Tenant context is missing!"}, status=status.HTTP_400_BAD_REQUEST)

        # ২. কাস্টমার ইউজার চিহ্নিত করা
        customer = None
        if request.user and request.user.is_authenticated:
            customer = request.user
        else:
            user_id = request.data.get('user_id') or request.data.get('customer_id')
            email = request.data.get('email')
            if user_id:
                customer = User.objects.filter(id=user_id).first()
            elif email:
                customer = User.objects.filter(email__iexact=email).first()

        if not customer:
            return Response({"error": "Authentication required! Please sign in."}, status=status.HTTP_401_UNAUTHORIZED)

        # ৩. স্টোরের মার্চেন্ট ইউজার চিহ্নিত করা
        merchant = (
            getattr(tenant, 'owner', None)
            or getattr(tenant, 'user', None)
            or User.objects.filter(is_superuser=True).first()
            or User.objects.filter(is_staff=True).first()
            or User.objects.filter(role__in=['merchant', 'owner', 'admin']).exclude(id=customer.id).first()
        )

        if not merchant:
            return Response({"error": "Store merchant account not found!"}, status=status.HTTP_404_NOT_FOUND)

        if customer.id == merchant.id:
            return Response({"error": "Customer and merchant cannot be the same user."}, status=status.HTTP_400_BAD_REQUEST)

        # ৪. চ্যাটরুম তৈরি বা পূর্বের রুম ফেচ
        try:
            room, created = ChatRoom.objects.get_or_create(
                tenant=tenant,
                customer=customer,
                merchant=merchant,
            )
        except IntegrityError:
            room = ChatRoom.objects.filter(
                tenant=tenant,
                customer=customer,
                merchant=merchant,
            ).first()
            created = False

        # 🌟 ৫. নতুন রুম হলে স্বয়ংক্রিয় এআই ওয়েলকাম মেসেজ ডাটাবেসে তৈরি করা
        if created:
            store_name = getattr(tenant, 'name', None) or (tenant.subdomain.capitalize() if hasattr(tenant, 'subdomain') else "আমাদের শপ")
            welcome_text = (
                f"👋 স্বাগতম {customer.first_name or 'সম্মানিত গ্রাহক'}!\n"
                f"{store_name}-এর সরাসরি সাপোর্ট ও হেল্পডেস্কে আপনাকে স্বাগতম। আমি আপনার ভার্চুয়াল শপ অ্যাসিস্ট্যান্ট। "
                "যেকোনো পণ্যের বিবরণ, ডেলিভারি তথ্য বা অর্ডার ট্র্যাকিংয়ের জন্য (যেমন: #ORD-1234) আমাকে লিখে পাঠাতে পারেন।"
            )
            ChatMessage.objects.create(
                room=room,
                sender=merchant,
                text=welcome_text,
                message_type='text'
            )

        serializer = ChatRoomSerializer(room, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ChatMessageHistoryView(generics.ListAPIView):
    """নির্দিষ্ট রুমের মেসেজ হিস্ট্রি লোড করা"""
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        room_id = self.kwargs.get('room_id')
        return ChatMessage.objects.filter(room_id=room_id).order_by('created_at')


class ChatMessageMarkReadView(APIView):
    """রুমে প্রবেশ করলে অপর প্রান্তের পাঠানো মেসেজগুলো 'পঠিত' (is_read=True) হিসেবে মার্ক করা"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        updated_count = ChatMessage.objects.filter(
            room_id=room_id,
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)
        return Response({"status": "success", "marked_read_count": updated_count}, status=status.HTTP_200_OK)


class ChatFileUploadView(APIView):
    """রিয়েল-টাইম চ্যাটে যেকোনো ফাইল (ইমেজ, ভয়েস, পিডিএফ, ভিডিও) আপলোড করা"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id)
        except ChatRoom.DoesNotExist:
            return Response({"error": "Chat room not found!"}, status=status.HTTP_404_NOT_FOUND)

        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({"error": "No file uploaded!"}, status=status.HTTP_400_BAD_REQUEST)

        msg_type = request.data.get('type', 'document')

        msg = ChatMessage.objects.create(
            room=room,
            sender=request.user,
            file_attachment=uploaded_file,
            file_name=uploaded_file.name,
            file_size=uploaded_file.size,
            message_type=msg_type
        )

        serializer = ChatMessageSerializer(msg, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChatBotDirectQueryView(APIView):
    """REST API ফলব্যাক: WebSocket ছাড়া সরাসরি এআই বটের কাছে প্রশ্ন পাঠানো"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        query_text = request.data.get('text', '').strip()
        if not query_text:
            return Response({"error": "Text prompt is required"}, status=status.HTTP_400_BAD_REQUEST)

        tenant = getattr(request, 'tenant', None)
        schema_name = tenant.schema_name if tenant else 'public'

        try:
            from .ai_bot import EnterpriseAIBot
            bot_reply = EnterpriseAIBot.generate_ai_reply(
                room_id=room_id,
                customer_id=request.user.id,
                incoming_text=query_text,
                schema_name=schema_name
            )
            return Response(bot_reply, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)