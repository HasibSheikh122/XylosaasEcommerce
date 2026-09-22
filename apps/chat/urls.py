# apps/chat/urls.py
from django.urls import path
from .views import (
    ChatRoomListView, 
    ChatRoomCreateView, 
    ChatMessageHistoryView, 
    ChatFileUploadView,
    ChatMessageMarkReadView,
    ChatBotDirectQueryView
)

urlpatterns = [
    # ১. চ্যাট রুমের তালিকা
    path('rooms/', ChatRoomListView.as_view(), name='chat-room-list'),
    
    # ২. চ্যাট রুম তৈরি ও এআই ওয়েলকাম ট্রিগার
    path('rooms/create/', ChatRoomCreateView.as_view(), name='chat-room-create'),
    
    # ৩. নির্দিষ্ট রুমের মেসেজ হিস্ট্রি
    path('rooms/<int:room_id>/messages/', ChatMessageHistoryView.as_view(), name='chat-message-history'),
    
    # ৪. মেসেজ রিড হিসেবে মার্ক করা
    path('rooms/<int:room_id>/read/', ChatMessageMarkReadView.as_view(), name='chat-message-mark-read'),
    
    # ৫. রিয়েল-টাইম ফাইল আপলোড
    path('rooms/<int:room_id>/upload/', ChatFileUploadView.as_view(), name='chat-file-upload'),

    # ৬. সরাসরি এআই বট কোয়েরি (REST ফলব্যাক)
    path('rooms/<int:room_id>/bot-ask/', ChatBotDirectQueryView.as_view(), name='chat-bot-direct-query'),
]