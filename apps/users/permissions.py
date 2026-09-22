from rest_framework import permissions

class IsMerchantOrTenantStaff(permissions.BasePermission):
    """শুধুমাত্র স্টোর ওনার, মার্চেন্ট অথবা স্টাফদের জন্য অনুমোদিত"""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # কাস্টমারদের সরাসরি ব্লক করা
        if getattr(request.user, 'role', '') == 'customer':
            return False

        if request.user.is_superuser:
            return True

        # টেন্যান্ট ম্যাচিং
        tenant = getattr(request, 'tenant', None)
        if tenant and getattr(request.user, 'tenant', None):
            return request.user.tenant == tenant

        return getattr(request.user, 'role', '') in ['merchant', 'admin', 'staff', 'owner']