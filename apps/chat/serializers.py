# apps/chat/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ChatRoom, ChatMessage, MessageReaction

User = get_user_model()

class ChatUserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'avatar']
        
    def get_name(self, obj):
        if obj.first_name:
            return f"{obj.first_name} {obj.last_name}".strip()
        return obj.email.split('@')[0]


class MessageReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageReaction
        fields = ['id', 'user', 'emoji', 'created_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_details = ChatUserSerializer(source='sender', read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'room', 'sender', 'sender_details', 'message_type', 
            'text', 'file_attachment', 'file_url', 'file_name', 
            'file_size', 'is_read', 'created_at', 'reactions'
        ]
        read_only_fields = ['sender', 'is_read', 'created_at']

    def get_file_url(self, obj):
        """মোবাইল ও রিভার্স প্রক্সির জন্য নিরাপদ মিডিয়া পাথ তৈরি"""
        if obj.file_attachment:
            return obj.file_attachment.url
        return None


class ChatRoomSerializer(serializers.ModelSerializer):
    customer_details = ChatUserSerializer(source='customer', read_only=True)
    merchant_details = ChatUserSerializer(source='merchant', read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'tenant', 'customer', 'customer_details', 
            'merchant', 'merchant_details', 'last_message', 
            'unread_count', 'updated_at'
        ]

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return {
                'text': last_msg.text,
                'message_type': last_msg.message_type,
                'created_at': last_msg.created_at,
                'sender_id': last_msg.sender_id
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0