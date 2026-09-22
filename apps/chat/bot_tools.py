# apps/chat/bot_tools.py
from django_tenants.utils import schema_context
from django.db.models import Q

def tool_search_products(schema_name, query, category=None, max_price=None, limit=4):
    """স্টোরের প্রোডাক্ট ডাটাবেস থেকে পণ্য সার্চ করার টুল"""
    with schema_context(schema_name):
        try:
            from apps.products.models import Product
            qs = Product.objects.filter(is_active=True)

            if query:
                qs = qs.filter(
                    Q(name__icontains=query) | 
                    Q(description__icontains=query) |
                    Q(tags__icontains=query)
                )
            if category:
                qs = qs.filter(category__name__icontains=category)
            if max_price:
                qs = qs.filter(price__lte=float(max_price))

            products = qs[:limit]
            if not products.exists():
                return {"status": "empty", "message": "কোনো পণ্য খুঁজে পাওয়া যায়নি।"}

            result = []
            for p in products:
                result.append({
                    "id": p.id,
                    "name": p.name,
                    "price": f"৳{p.price}",
                    "in_stock": getattr(p, 'stock', 1) > 0,
                    "url": f"/products/{getattr(p, 'slug', p.id)}"
                })
            return {"status": "success", "products": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}


def tool_get_order_details(schema_name, customer_id, order_number=None):
    """গ্রাহকের অর্ডার ও বর্তমান অবস্থা জানার টুল"""
    with schema_context(schema_name):
        try:
            from apps.orders.models import Order
            qs = Order.objects.filter(customer_id=customer_id)

            if order_number:
                order = qs.filter(order_number__icontains=order_number.strip()).first()
            else:
                order = qs.order_by('-created_at').first()

            if not order:
                return {"status": "not_found", "message": "কোনো অর্ডার পাওয়া যায়নি।"}

            items = []
            for item in order.items.all()[:3]:
                items.append({
                    "name": getattr(item, 'product_name', 'Item'),
                    "quantity": item.quantity,
                    "price": f"৳{item.price}"
                })

            return {
                "status": "success",
                "order_number": order.order_number,
                "current_status": order.status,
                "total": f"৳{order.total}",
                "items": items,
                "created_at": order.created_at.strftime("%d %b, %Y")
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


def tool_get_store_policies(schema_name, topic="general"):
    """স্টোরের ডেলিভারি চার্জ, রিটার্ন ও পেমেন্ট পলিসি জানার টুল"""
    with schema_context(schema_name):
        return {
            "delivery": "ঢাকার ভেতরে ২৪-৪৮ ঘণ্টা (৬০ টাকা), ঢাকার বাইরে ৩-৫ দিন (১২০ টাকা)।",
            "return_policy": "পণ্য হাতে পাওয়ার ৭ দিনের মধ্যে ত্রুটি থাকলে সম্পূর্ণ ফ্রি রিটার্ন বা রিফান্ড প্রযোজ্য।",
            "payment_methods": "ক্যাশ অন ডেলিভারি (COD), বিকাশ, নগদ ও কার্ড পেমেন্ট গ্রহণযোগ্য।"
        }