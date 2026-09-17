from celery import shared_task
from django_tenants.utils import schema_context
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_order_confirmation_email(self, schema_name, order_id):
    """
    নির্দিষ্ট টেন্যান্ট স্কিমার ভেতরে ঢুকে কাস্টমার ও স্টোর ওনারকে অর্ডার ইমেইল পাঠানোর ব্যাকগ্রাউন্ড টাস্ক
    """
    with schema_context(schema_name):
        from apps.orders.models import Order
        from apps.stores.models import StoreSettings

        try:
            order = Order.objects.select_related('tenant').prefetch_related('items').get(id=order_id)
            store_settings = StoreSettings.objects.filter(tenant=order.tenant).first()
            store_name = store_settings.store_name if store_settings else order.tenant.store_name

            customer_email = order.shipping_address.get('email') or (order.customer.email if order.customer else None)
            if not customer_email:
                logger.warning(f"No email found for Order #{order.order_number}")
                return f"Skipped: No email for Order #{order.order_number}"

            subject = f"অর্ডার কনফার্মেশন - {order.order_number} ({store_name})"
            items_list = "\n".join([f"- {item.product_name} x {item.quantity} = ৳{item.total_price}" for item in order.items.all()])
            
            message = (
                f"প্রিয় গ্রাহক,\n\n"
                f"{store_name}-এ আপনার অর্ডারটি সফলভাবে গ্রহণ করা হয়েছে!\n\n"
                f"অর্ডার নাম্বার: {order.order_number}\n"
                f"মোট বিল: ৳{order.total}\n"
                f"পেমেন্ট মেথড: {order.payment_method.upper()}\n\n"
                f"অর্ডার আইটেমস:\n{items_list}\n\n"
                f"ধন্যবাদ,\n{store_name} টিম"
            )

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[customer_email],
                fail_silently=False,
            )
            return f"Email sent successfully for Order #{order.order_number}"

        except Order.DoesNotExist:
            logger.error(f"Order #{order_id} not found in schema {schema_name}")
            return f"Order not found: {order_id}"
        except Exception as exc:
            logger.error(f"Failed to send email for Order #{order_id}: {str(exc)}")
            raise self.retry(exc=exc, countdown=60)