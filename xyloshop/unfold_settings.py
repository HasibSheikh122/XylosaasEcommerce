from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

# মডুলার নেভিগেশন (কোড কমানোর জন্য লুপ বা লিস্ট ব্যবহার করুন)
def get_nav_items():
    return [
        {"title": _("Dashboard"), "icon": "dashboard", "link": reverse_lazy("admin:index")},
        {"title": _("Analytics"), "icon": "analytics", "link": reverse_lazy("admin:analytics_salesanalytics_changelist")},
    ]

UNFOLD_CONFIG = {
    "SITE_TITLE": _("ShopHive AI · Enterprise"),
    "SITE_HEADER": _("✨ ShopHive AI"),
    "THEME": "dark",
    
    # সংক্ষেপে কালার প্যালেট
    "COLORS": {
        "primary": {"500": "16 185 129"},
        "secondary": {"500": "168 85 247"},
    },

    # ড্যাশবোর্ড স্ট্যাটস
    "DASHBOARD": {
        "stats": [
            {"title": _("Tenants"), "icon": "storefront", "link": reverse_lazy("admin:tenants_tenant_changelist")},
            {"title": _("Orders"), "icon": "shopping_cart", "link": reverse_lazy("admin:orders_order_changelist")},
        ],
    },

    # সাইডবার (ক্লিন এবং সংক্ষিপ্ত)
    "SIDEBAR": {
        "navigation": [
            {"title": _("Core"), "items": get_nav_items()},
            {"title": _("Management"), "separator": True, "items": [
                {"title": _("Tenants"), "icon": "storefront", "link": reverse_lazy("admin:tenants_tenant_changelist")},
                {"title": _("Products"), "icon": "inventory_2", "link": reverse_lazy("admin:products_product_changelist")},
            ]},
        ],
    },

    # স্টাইলস (ফাইল রেফারেন্স ব্যবহার করুন, সরাসরি কোড নয়)
    "STYLES": ["css/cinematic-admin.css"],
}