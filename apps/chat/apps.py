# apps/chat/apps.py
from django.apps import AppConfig

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.chat'  # 🌟 এখানে শুধু 'chat' থাকলে তা পরিবর্তন করে 'apps.chat' দিন