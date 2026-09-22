# apps/stores/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StoreBannerViewSet,
    StoreTestimonialViewSet,
    StoreBlogPostViewSet,
    StoreFAQViewSet,
    StoreNewsletterSubscriberViewSet,
    StoreSettingsView,
    MerchantPasswordChangeView,
    MerchantSubscriptionView,
    SuperAdminNotificationsView,
    StoreCategoryListView,
    StoreNewsletterCreateView,
    StorefrontHomeView,
    ThemeMarketplaceView,  # 🌟 ইমপোর্ট যোগ করা হয়েছে
    ThemeActionView,       # 🌟 ইমপোর্ট যোগ করা হয়েছে
)

router = DefaultRouter()
router.register(r'banners', StoreBannerViewSet, basename='store-banner')
router.register(r'testimonials', StoreTestimonialViewSet, basename='store-testimonial')
router.register(r'blogs', StoreBlogPostViewSet, basename='store-blog')
router.register(r'faqs', StoreFAQViewSet, basename='store-faq')
router.register(r'subscribers', StoreNewsletterSubscriberViewSet, basename='store-subscriber')

urlpatterns = [
    path('home-data/', StorefrontHomeView.as_view(), name='storefront-home'),
    path('settings/', StoreSettingsView.as_view(), name='store-settings'),
    path('merchant/change-password/', MerchantPasswordChangeView.as_view(), name='change-password'),
    path('merchant/subscription/', MerchantSubscriptionView.as_view(), name='merchant-subscription'),
    path('merchant/admin-notifications/', SuperAdminNotificationsView.as_view(), name='admin-notifications'),
    path('categories/', StoreCategoryListView.as_view(), name='store-categories'),
    path('newsletter/', StoreNewsletterCreateView.as_view(), name='store-newsletter'),
    path('marketplace/themes/', ThemeMarketplaceView.as_view(), name='theme-marketplace'),
    path('marketplace/themes/action/', ThemeActionView.as_view(), name='theme-action'),
    path('', include(router.urls)),

]
