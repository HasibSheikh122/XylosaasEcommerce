from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    # ১. অ্যাডমিন প্যানেলের মেইন টেবিলে যে যে কলাম দেখতে পাবেন
    list_display = ('username', 'email', 'role', 'tenant', 'is_staff', 'created_at')
    
    # ২. ডানপাশে যে ফিল্টারগুলো থাকবে (সহজে ডেটা ফিল্টার করার জন্য)
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'created_at')
    
    # ৩. সার্চ বক্স দিয়ে যা যা সার্চ করা যাবে
    search_fields = ('username', 'email', 'phone')
    
    # ৪. তৈরি করার তারিখ অনুযায়ী সর্টিং হবে (নতুন ইউজার সবার উপরে থাকবে)
    ordering = ('-created_at',)

    # ৫. ইউজারের ভেতরে ঢুকলে ফিল্ডগুলো যেভাবে সাজানো থাকবে (Fieldsets)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar', 'bio')}),
        (_('Role & Multi-Tenant'), {'fields': ('role', 'tenant')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Settings & Metadata'), {'fields': ('timezone', 'email_notifications', 'push_notifications', 'last_login_ip', 'last_login_device')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # ৬. নতুন ইউজার বানানোর সময় যে ফিল্ডগুলো লাগবে
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'role', 'tenant', 'phone'),
        }),
    )

    # readonly_fields যাতে কেউ অ্যাডমিন থেকে ভুল করে আইপি বা ডিভাইস এডিট করতে না পারে
    readonly_fields = ('last_login_ip', 'last_login_device')