from django.core.cache import cache
from .models import StoreSettings

class StoreService:
    @staticmethod
    def get_settings(tenant):
        cache_key = f'tenant_{tenant.id}_settings'
        settings = cache.get(cache_key)
        if not settings:
            settings = StoreSettings.objects.get_or_create(tenant=tenant)[0]
            cache.set(cache_key, settings, timeout=3600)
        return settings

    @staticmethod
    def invalidate_settings(tenant):
        cache.delete(f'tenant_{tenant.id}_settings')

    @staticmethod
    def update_branding(tenant, data):
        settings = StoreSettings.objects.get(tenant=tenant)
        for attr, value in data.items():
            setattr(settings, attr, value)
        settings.save()
        StoreService.invalidate_settings(tenant)
        return settings