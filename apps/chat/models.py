# apps/chat/models.py
from django.db import models
from django.conf import settings

class ChatRoom(models.Model):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='chat_rooms')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_rooms')
    merchant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='merchant_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'customer', 'merchant')

    def __str__(self):
        return f"Chat: {self.customer.email} <-> {self.merchant.email}"


class ChatMessage(models.Model):
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('audio', 'Audio/Voice Note'),
        ('video', 'Video'),
        ('document', 'Document/File'),
        ('call', 'Call Log'),  # 🌟 Call history ebong duration tracking er jonno
    )

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    text = models.TextField(blank=True, null=True)
    file_attachment = models.FileField(upload_to='chat_attachments/%Y/%m/', blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.IntegerField(blank=True, null=True)  # Call duration (seconds) hishebeo use hobe
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class MessageReaction(models.Model):
    """WhatsApp-style emoji reaction (e.g. ❤️, 👍, 😂, 😮, 😢)"""
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user')