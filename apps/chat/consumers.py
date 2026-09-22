# apps/chat/consumers.py
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from .models import ChatRoom, ChatMessage, MessageReaction

User = get_user_model()
logger = logging.getLogger(__name__)

class ChatAndCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f"chat_{self.room_id}"

        # সাবডোমেন অনুযায়ী টেন্যান্ট স্কিমা নির্ণয়
        headers = dict(self.scope['headers'])
        host = headers.get(b'host', b'').decode('utf-8')
        subdomain = host.split('.')[0] if '.' in host else 'public'
        
        self.schema_name = await self.get_schema_name(subdomain)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action_type = data.get('type')

        # ১. রিয়েল-টাইম টেক্সট মেসেজ ও AI বট
        if action_type == 'chat_message':
            msg_obj = await self.save_text_message(data)
            if msg_obj:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'broadcast_message',
                        'message': msg_obj
                    }
                )

                # গ্রাহক মেসেজ পাঠালে AI বট সক্রিয় হবে
                sender_id = data.get('sender_id')
                merchant_id = await self.get_merchant_id()

                if merchant_id and str(sender_id) != str(merchant_id):
                    # বট টাইপিং ইন্ডিকেটর অন
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'broadcast_typing',
                            'sender_id': 'bot',
                            'is_typing': True
                        }
                    )

                    bot_reply = None
                    try:
                        from .ai_bot import EnterpriseAIBot
                        bot_reply = await EnterpriseAIBot.generate_ai_reply(
                            room_id=self.room_id,
                            customer_id=sender_id,
                            incoming_text=data.get('text', ''),
                            schema_name=self.schema_name
                        )
                    except Exception as e:
                        logger.error(f"Enterprise AI Bot error: {e}")

                    # বট টাইপিং ইন্ডিকেটর অফ
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'broadcast_typing',
                            'sender_id': 'bot',
                            'is_typing': False
                        }
                    )

                    if bot_reply:
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'broadcast_message',
                                'message': bot_reply
                            }
                        )

        # ২. ফাইল আপলোড ব্রডকাস্ট
        elif action_type == 'chat_file':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_message',
                    'message': data.get('message')
                }
            )

        # ৩. কল শেষ বা বাতিল (Call Log সেভ করা)
        elif action_type in ['call_ended', 'call_rejected']:
            payload = data.get('data', {})
            call_log_msg = await self.save_call_log(payload)
            if call_log_msg:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'broadcast_message',
                        'message': call_log_msg
                    }
                )
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_call_signal',
                    'signal_type': action_type,
                    'sender_channel_name': self.channel_name,
                    'data': payload
                }
            )

        # ৪. ইমোজি রিঅ্যাকশন
        elif action_type == 'message_reaction':
            reaction_data = await self.save_reaction(data)
            if reaction_data:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'broadcast_reaction',
                        'reaction': reaction_data
                    }
                )

        # ৫. টাইপিং ইন্ডিকেটর
        elif action_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_typing',
                    'sender_id': data.get('sender_id'),
                    'is_typing': data.get('is_typing')
                }
            )

        # ৬. WebRTC সিগন্যালিং
        elif action_type in ['call_offer', 'call_answer', 'ice_candidate']:
            payload = data.get('data', data)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_call_signal',
                    'signal_type': action_type,
                    'sender_channel_name': self.channel_name,
                    'data': payload
                }
            )

    # ---------------------------------------------------------
    # Channel Layer Event Handlers
    # ---------------------------------------------------------
    async def broadcast_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def broadcast_reaction(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_reaction',
            'reaction': event['reaction']
        }))

    async def broadcast_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'sender_id': event['sender_id'],
            'is_typing': event['is_typing']
        }))

    async def broadcast_call_signal(self, event):
        if event.get('sender_channel_name') == self.channel_name:
            return

        await self.send(text_data=json.dumps({
            'type': event['signal_type'],
            'data': event['data']
        }))

    # ---------------------------------------------------------
    # Database Operations
    # ---------------------------------------------------------
    @database_sync_to_async
    def get_schema_name(self, subdomain):
        try:
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.get(subdomain__iexact=subdomain)
            return tenant.schema_name
        except Exception:
            return 'public'

    @database_sync_to_async
    def get_merchant_id(self):
        with schema_context(self.schema_name):
            room = ChatRoom.objects.filter(id=self.room_id).first()
            return room.merchant_id if room else None

    @database_sync_to_async
    def save_text_message(self, data):
        with schema_context(self.schema_name):
            sender_id = data.get('sender_id')
            sender = User.objects.filter(id=sender_id).first()
            room = ChatRoom.objects.filter(id=self.room_id).first()
            if not sender or not room:
                return None

            msg = ChatMessage.objects.create(
                room=room,
                sender=sender,
                text=data.get('text', ''),
                message_type='text'
            )
            return {
                'id': msg.id,
                'room': room.id,
                'sender': sender.id,
                'sender_id': sender.id,
                'sender_details': {
                    'id': sender.id,
                    'name': f"{sender.first_name} {sender.last_name}".strip() or sender.email,
                    'email': sender.email
                },
                'text': msg.text,
                'file_url': None,
                'file_name': None,
                'file_size': None,
                'message_type': 'text',
                'created_at': msg.created_at.isoformat()
            }

    @database_sync_to_async
    def save_call_log(self, call_data):
        with schema_context(self.schema_name):
            sender_id = call_data.get('sender_id')
            if not sender_id:
                return None
            sender = User.objects.filter(id=sender_id).first()
            room = ChatRoom.objects.filter(id=self.room_id).first()
            if not sender or not room:
                return None

            call_type = call_data.get('call_type', 'audio')
            status = call_data.get('status', 'completed')
            duration = int(call_data.get('duration', 0))

            if status == 'cancelled':
                log_text = f"Cancelled {call_type} call"
            elif status == 'missed':
                log_text = f"Missed {call_type} call"
            else:
                hours = duration // 3600
                minutes = (duration % 3600) // 60
                seconds = duration % 60
                dur_parts = []
                if hours > 0:
                    dur_parts.append(f"{hours} hr")
                if minutes > 0:
                    dur_parts.append(f"{minutes} min")
                dur_parts.append(f"{seconds} sec")
                dur_str = " ".join(dur_parts)
                log_text = f"{call_type.capitalize()} call • {dur_str}"

            msg = ChatMessage.objects.create(
                room=room,
                sender=sender,
                text=log_text,
                message_type='call',
                file_size=duration
            )

            return {
                'id': msg.id,
                'room': room.id,
                'sender': sender.id,
                'sender_id': sender.id,
                'text': msg.text,
                'message_type': 'call',
                'call_status': status,
                'file_size': duration,
                'created_at': msg.created_at.isoformat()
            }

    @database_sync_to_async
    def save_reaction(self, data):
        with schema_context(self.schema_name):
            user = User.objects.filter(id=data.get('user_id')).first()
            msg = ChatMessage.objects.filter(id=data.get('message_id')).first()
            if not user or not msg:
                return None
            reaction, _ = MessageReaction.objects.update_or_create(
                message=msg,
                user=user,
                defaults={'emoji': data['emoji']}
            )
            return {
                'message_id': msg.id,
                'user_id': user.id,
                'emoji': reaction.emoji
            }