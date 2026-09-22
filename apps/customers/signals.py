# apps/customers/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Customer

User = get_user_model()


@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    """User create hole customer profile automatically sync kora"""
    if created and getattr(instance, 'tenant', None):
        user_phone = getattr(instance, 'phone', '') or ''
        Customer.objects.get_or_create(
            tenant=instance.tenant,
            email=instance.email.strip().lower(),
            defaults={
                'user': instance,
                'first_name': instance.first_name,
                'last_name': instance.last_name,
                'phone': user_phone,
            }
        )