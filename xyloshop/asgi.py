# xyloshop/asgi.py (আপনার প্রজেক্টের ফোল্ডারের নাম অনুযায়ী)
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xyloshop.settings')

# 🌟 ১. Django-এর অ্যাপগুলো আগে লোড করার জন্য এটি আগে কল করতে হবে
django_asgi_app = get_asgi_application()

# 🌟 ২. অ্যাপ লোড হওয়ার পর Channels এবং routing ইমপোর্ট করতে হবে
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import apps.chat.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            apps.chat.routing.websocket_urlpatterns
        )
    ),
})