from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):

    list_display = (
        'email',
        'first_name',
        'last_name',
        'role',
        'tenant',
        'is_staff',
        'created_at',
    )

    list_filter = (
        'role',
        'is_staff',
        'is_superuser',
        'is_active',
        'created_at',
    )

    search_fields = (
        'email',
        'first_name',
        'last_name',
        'phone',
    )

    ordering = ('-created_at',)

    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),

        (_('Personal info'), {
            'fields': (
                'first_name',
                'last_name',
                'phone',
                'avatar',
                'bio',
            )
        }),

        (_('Role & Multi-Tenant'), {
            'fields': (
                'role',
                'tenant',
            )
        }),

        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),

        (_('Settings & Metadata'), {
            'fields': (
                'timezone',
                'email_notifications',
                'push_notifications',
                'last_login_ip',
                'last_login_device',
            )
        }),

        (_('Important dates'), {
            'fields': (
                'last_login',
                'date_joined',
                'created_at',
                'updated_at',
            )
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'role',
                'tenant',
                'phone',
                'is_staff',
                'is_active',
            ),
        }),
    )

    readonly_fields = (
        'last_login_ip',
        'last_login_device',
        'created_at',
        'updated_at',
    )