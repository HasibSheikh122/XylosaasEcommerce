from django.db import connection
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django_tenants.utils import get_public_schema_name

User = get_user_model()


@receiver(post_save, sender=User)
def handle_user_post_save(sender, instance, created, **kwargs):
    """
    ইউজার তৈরির পর প্রোফাইল সিঙ্ক সিগন্যাল
    """
    # ১. পাবলিক স্কিমায় থাকলে সিগন্যাল সম্পূর্ণ বন্ধ থাকবে (পাবলিক স্কিমায় কাস্টমার টেবিল থাকে না)
    try:
        public_schema = get_public_schema_name()
        if connection.schema_name == public_schema:
            return
    except Exception:
        pass

    # ২. ইউজার যদি মার্চেন্ট, স্টাফ বা সুপার অ্যাডমিন হয়, তবে কাস্টমার প্রোফাইল তৈরি হবে না
    user_role = getattr(instance, 'role', '')
    if user_role in ['merchant', 'admin', 'super_admin', 'staff', 'owner', 'store_owner']:
        return

    # ৩. শুধুমাত্র টেন্যান্ট স্কিমার সাধারণ কাস্টমারদের জন্য প্রোফাইল তৈরি হবে
    if created and user_role == 'customer':
        try:
            from apps.customers.models import Customer
            tenant = getattr(instance, 'tenant', None)
            
            Customer.objects.get_or_create(
                user=instance,
                defaults={
                    'tenant': tenant,
                    'email': instance.email,
                    'first_name': instance.first_name,
                    'last_name': instance.last_name,
                    'phone': getattr(instance, 'phone', ''),
                }
            )
        except Exception:
            # কোনো স্কিমা মিসম্যাচ হলেও মূল রিকোয়েস্ট ক্র্যাশ করবে না
            pass