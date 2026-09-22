# apps/stores/views.py
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import generics, permissions, status, viewsets, views
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.serializers import ValidationError as DRFValidationError
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from .models import (
    StoreSettings,
    StoreCategory,
    StoreBanner,
    StoreFAQ,
    StoreTestimonial,
    StoreNewsletterSubscriber,
    StoreBlogPost
)
from .serializers import (
    StoreSettingsSerializer,
    StoreCategorySerializer,
    StoreBannerSerializer,
    StoreFAQSerializer,
    StoreTestimonialSerializer,
    StoreNewsletterSerializer,
    StoreBlogPostSerializer,
    StoreNewsletterSubscriberSerializer
)


class SafeJWTAuthentication(JWTAuthentication):
    """Token expired ba invalid holeo jate 401 diye request crash na kore"""
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except Exception:
            return None


class StoreBannerViewSet(viewsets.ModelViewSet):
    serializer_class = StoreBannerSerializer
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_tenant(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant and self.request.user and self.request.user.is_authenticated:
            tenant = getattr(self.request.user, 'tenant', None)
        if not tenant:
            host = self.request.get_host().split(':')[0]
            subdomain = host.split('.')[0]
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.filter(subdomain__iexact=subdomain).first()
        if not tenant:
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.first()
        return tenant

    def get_queryset(self):
        tenant = self.get_tenant()
        qs = StoreBanner.objects.all()
        if tenant:
            qs = qs.filter(tenant=tenant)
        
        banner_type = self.request.query_params.get('type')
        if banner_type and banner_type != 'all':
            qs = qs.filter(banner_type=banner_type)
            
        return qs.order_by('display_order', '-created_at')

    def perform_create(self, serializer):
        tenant = self.get_tenant()
        try:
            serializer.save(tenant=tenant)
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))

    def perform_update(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))

    @action(detail=True, methods=['post', 'patch'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        banner = self.get_object()
        banner.is_active = not banner.is_active
        try:
            banner.save()
            return Response({
                'message': f"Banner {'active' if banner.is_active else 'inactive'} kora hoyeche.",
                'is_active': banner.is_active
            }, status=status.HTTP_200_OK)
        except DjangoValidationError as e:
            return Response(
                {'detail': e.message_dict if hasattr(e, 'message_dict') else str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class StoreSettingsView(APIView):
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def get_tenant(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant and self.request.user and self.request.user.is_authenticated:
            tenant = getattr(self.request.user, 'tenant', None)

        host = self.request.get_host().split(':')[0]
        subdomain = host.split('.')[0] if '.' in host else 'nextlook'
        if subdomain in ['localhost', '127', 'api']:
            subdomain = self.request.query_params.get('subdomain') or 'nextlook'

        from apps.tenants.models import Tenant
        tenant_fields = [f.name for f in Tenant._meta.fields]

        if not tenant and 'subdomain' in tenant_fields:
            tenant = Tenant.objects.filter(subdomain__iexact=subdomain).first()
        if not tenant and 'schema_name' in tenant_fields:
            tenant = Tenant.objects.filter(schema_name__iexact=subdomain).first()
        if not tenant and 'slug' in tenant_fields:
            tenant = Tenant.objects.filter(slug__iexact=subdomain).first()
        if not tenant and 'name' in tenant_fields:
            tenant = Tenant.objects.filter(name__iexact=subdomain).first()

        if not tenant:
            tenant = Tenant.objects.first()

        if not tenant:
            create_kwargs = {}
            if 'name' in tenant_fields:
                create_kwargs['name'] = subdomain.capitalize()
            if 'subdomain' in tenant_fields:
                create_kwargs['subdomain'] = subdomain
            if 'schema_name' in tenant_fields:
                create_kwargs['schema_name'] = subdomain
            if 'slug' in tenant_fields:
                create_kwargs['slug'] = subdomain
            tenant = Tenant.objects.create(**create_kwargs)

        return tenant

    def get_object(self):
        tenant = self.get_tenant()
        settings = StoreSettings.objects.filter(tenant=tenant).first()

        if not settings:
            settings = StoreSettings.objects.first()
            if settings and not settings.tenant:
                settings.tenant = tenant
                settings.save(update_fields=['tenant'])

        if not settings:
            sub = getattr(tenant, 'subdomain', None) or getattr(tenant, 'slug', None) or 'nextlook'
            settings = StoreSettings.objects.create(
                tenant=tenant,
                store_name=getattr(tenant, 'name', 'My Store') or 'My Store',
                subdomain=sub,
                primary_color='#059669',
                secondary_color='#047857',
                font_family='Poppins',
                show_announcement_bar=True,
                announcement_text='Sign up and GET 20% OFF on your first order!',
                announcement_phone='+880 1700-000000',
            )

        return settings

    def get(self, request):
        settings = self.get_object()
        serializer = StoreSettingsSerializer(settings, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        settings = self.get_object()
        tenant = self.get_tenant()
        
        if not settings.tenant:
            settings.tenant = tenant

        data = request.data
        updatable_fields = [
            'primary_color', 'secondary_color', 'accent_color',
            'font_family', 'show_announcement_bar', 'announcement_text',
            'announcement_phone', 'theme', 'store_name', 'store_tagline',
            'store_description', 'contact_email', 'contact_phone', 'contact_address',
            'currency', 'currency_symbol'
        ]

        for field in updatable_fields:
            if field in data:
                val = data.get(field)
                if hasattr(settings, field):
                    try:
                        setattr(settings, field, val)
                    except Exception:
                        pass

        try:
            settings.save()
        except Exception:
            if hasattr(settings, 'theme'):
                settings.theme = 'default'
            settings.save()

        serializer = StoreSettingsSerializer(settings, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


StoreSettingsUpdateView = StoreSettingsView


class StoreCategoryListView(generics.ListAPIView):
    serializer_class = StoreCategorySerializer
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return StoreCategory.objects.filter(is_active=True, show_on_homepage=True)


class StoreBannerListView(generics.ListAPIView):
    serializer_class = StoreBannerSerializer
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = StoreBanner.objects.filter(is_active=True)
        banner_type = self.request.query_params.get('type')
        if banner_type:
            queryset = queryset.filter(banner_type=banner_type)
        return queryset


class StoreFAQListView(generics.ListAPIView):
    serializer_class = StoreFAQSerializer
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]
    queryset = StoreFAQ.objects.filter(is_active=True)


class StoreTestimonialListView(generics.ListAPIView):
    serializer_class = StoreTestimonialSerializer
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]
    queryset = StoreTestimonial.objects.filter(is_featured=True)


class StoreBlogPostListView(generics.ListAPIView):
    serializer_class = StoreBlogPostSerializer
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]
    queryset = StoreBlogPost.objects.filter(is_published=True)[:3]


class StorefrontHomeView(APIView):
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        settings = StoreSettings.objects.first()
        categories = StoreCategory.objects.filter(is_active=True, show_on_homepage=True)
        banners = StoreBanner.objects.filter(is_active=True)
        faqs = StoreFAQ.objects.filter(is_active=True)
        testimonials = StoreTestimonial.objects.filter(is_featured=True)
        blogs = StoreBlogPost.objects.filter(is_published=True)[:3]

        def get_single_banner(b_type):
            item = banners.filter(banner_type=b_type).first()
            return StoreBannerSerializer(item, context={'request': request}).data if item else None

        return Response({
            'settings': StoreSettingsSerializer(settings, context={'request': request}).data if settings else None,
            'categories': StoreCategorySerializer(categories, many=True, context={'request': request}).data,
            'banners': {
                'hero': StoreBannerSerializer(
                    banners.filter(banner_type='hero')[:3], 
                    many=True, 
                    context={'request': request}
                ).data,
                'countdown': get_single_banner('countdown'),
                'weekly': get_single_banner('weekly'),
                'dual_promos': StoreBannerSerializer(
                    banners.filter(banner_type='dual_promo')[:2], 
                    many=True, 
                    context={'request': request}
                ).data,
                'deal_of_day': get_single_banner('deal_of_day'),
                'wide_offer': get_single_banner('wide_offer'),
            },
            'faqs': StoreFAQSerializer(faqs, many=True).data,
            'testimonials': StoreTestimonialSerializer(testimonials, many=True, context={'request': request}).data,
            'blogs': StoreBlogPostSerializer(blogs, many=True, context={'request': request}).data,
        })


class StoreTestimonialViewSet(viewsets.ModelViewSet):
    serializer_class = StoreTestimonialSerializer
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_tenant(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant and self.request.user and self.request.user.is_authenticated:
            tenant = getattr(self.request.user, 'tenant', None)
        if not tenant:
            host = self.request.get_host().split(':')[0]
            subdomain = host.split('.')[0]
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.filter(subdomain__iexact=subdomain).first()
        if not tenant:
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.first()
        return tenant

    def get_queryset(self):
        tenant = self.get_tenant()
        qs = StoreTestimonial.objects.all()
        if tenant:
            qs = qs.filter(tenant=tenant)

        is_admin = self.request.query_params.get('admin') == 'true'
        if self.action == 'list' and not is_admin:
            qs = qs.filter(is_featured=True)

        return qs.order_by('display_order', '-created_at')

    def perform_create(self, serializer):
        tenant = self.get_tenant()
        serializer.save(tenant=tenant)

    def perform_update(self, serializer):
        tenant = self.get_tenant()
        if tenant:
            serializer.save(tenant=tenant)
        else:
            serializer.save()

    @action(detail=True, methods=['post', 'patch'], url_path='toggle-featured')
    def toggle_featured(self, request, pk=None):
        tenant = self.get_tenant()
        qs = StoreTestimonial.objects.all()
        if tenant:
            qs = qs.filter(tenant=tenant)
            
        testimonial = qs.filter(pk=pk).first()
        if not testimonial:
            return Response({'detail': 'Testimonial paowa jayni.'}, status=status.HTTP_404_NOT_FOUND)

        testimonial.is_featured = not testimonial.is_featured
        testimonial.save(update_fields=['is_featured'])

        return Response({
            'message': f"Testimonial {'active' if testimonial.is_featured else 'hidden'} kora hoyeche.",
            'is_featured': testimonial.is_featured
        }, status=status.HTTP_200_OK)


class StoreBlogPostViewSet(viewsets.ModelViewSet):
    serializer_class = StoreBlogPostSerializer
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_tenant(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant and self.request.user and self.request.user.is_authenticated:
            tenant = getattr(self.request.user, 'tenant', None)
        if not tenant:
            host = self.request.get_host().split(':')[0]
            subdomain = host.split('.')[0]
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.filter(subdomain__iexact=subdomain).first()
        if not tenant:
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.first()
        return tenant

    def get_queryset(self):
        tenant = self.get_tenant()
        qs = StoreBlogPost.objects.all()
        if tenant:
            qs = qs.filter(tenant=tenant)

        is_admin = self.request.query_params.get('admin') == 'true'
        if self.action == 'list' and not is_admin:
            qs = qs.filter(is_published=True)

        return qs.order_by('-published_at', '-created_at')

    def perform_create(self, serializer):
        tenant = self.get_tenant()
        serializer.save(tenant=tenant)

    def perform_update(self, serializer):
        tenant = self.get_tenant()
        if tenant:
            serializer.save(tenant=tenant)
        else:
            serializer.save()

    @action(detail=True, methods=['post', 'patch'], url_path='toggle-publish')
    def toggle_publish(self, request, pk=None):
        tenant = self.get_tenant()
        qs = StoreBlogPost.objects.all()
        if tenant:
            qs = qs.filter(tenant=tenant)

        post = qs.filter(pk=pk).first()
        if not post:
            return Response({'detail': 'Blog post paoa jayni.'}, status=status.HTTP_404_NOT_FOUND)

        post.is_published = not post.is_published
        post.save(update_fields=['is_published', 'updated_at'])

        return Response({
            'message': f"Blog post {'published' if post.is_published else 'draft'} kora hoyeche.",
            'is_published': post.is_published
        }, status=status.HTTP_200_OK)


class StoreFAQViewSet(viewsets.ModelViewSet):
    serializer_class = StoreFAQSerializer
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def get_tenant(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant and self.request.user and self.request.user.is_authenticated:
            tenant = getattr(self.request.user, 'tenant', None)
        if not tenant:
            host = self.request.get_host().split(':')[0]
            subdomain = host.split('.')[0]
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.filter(subdomain__iexact=subdomain).first()
        return tenant or Tenant.objects.first()

    def get_queryset(self):
        tenant = self.get_tenant()
        qs = StoreFAQ.objects.all()
        if tenant:
            qs = qs.filter(tenant=tenant)
        return qs.order_by('display_order', 'id')

    def perform_create(self, serializer):
        tenant = self.get_tenant()
        serializer.save(tenant=tenant)


class StoreNewsletterCreateView(APIView):
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email or '@' not in email:
            return Response({'detail': 'Sothik email address prodan korun.'}, status=status.HTTP_400_BAD_REQUEST)

        host = request.get_host().split(':')[0]
        subdomain = host.split('.')[0]
        from apps.tenants.models import Tenant
        tenant = getattr(request, 'tenant', None) or Tenant.objects.filter(subdomain__iexact=subdomain).first() or Tenant.objects.first()

        subscriber, created = StoreNewsletterSubscriber.objects.get_or_create(
            tenant=tenant,
            email=email
        )

        return Response(
            {
                'message': 'Shofolbhabe subscribe kora hoyeche!' if created else 'Apni itomodde subscribe korechen.',
                'created': created
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class StoreNewsletterSubscriberViewSet(viewsets.ModelViewSet):
    serializer_class = StoreNewsletterSubscriberSerializer
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def get_tenant(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant and self.request.user and self.request.user.is_authenticated:
            tenant = getattr(self.request.user, 'tenant', None)
        if not tenant:
            host = self.request.get_host().split(':')[0]
            subdomain = host.split('.')[0]
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.filter(subdomain__iexact=subdomain).first()
        return tenant or Tenant.objects.first()

    def get_queryset(self):
        tenant = self.get_tenant()
        qs = StoreNewsletterSubscriber.objects.all()
        if tenant and hasattr(StoreNewsletterSubscriber, 'tenant'):
            qs = qs.filter(tenant=tenant)
        return qs.order_by('-id')

class MerchantPasswordChangeView(views.APIView):
    """মার্চেন্ট পাসওয়ার্ড পরিবর্তন ও ইনস্ট্যান্ট হ্যাশিং API (মাল্টি-টেন্যান্ট পাবলিক স্কিমা সিঙ্ক সহ)"""
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from django.contrib.auth import get_user_model
        from django_tenants.utils import schema_context, get_public_schema_name
        User = get_user_model()

        data = request.data
        new_password = (
            data.get("new_password") 
            or data.get("newPassword") 
            or data.get("password") 
            or ""
        ).strip()

        if not new_password or len(new_password) < 6:
            return Response(
                {"detail": "নতুন পাসওয়ার্ড দেওয়া আবশ্যক এবং তা কমপক্ষে ৬ অক্ষরের হতে হবে।"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        email_from_req = (data.get("email") or "").strip().lower()
        enable_2fa = data.get("enable_2fa") if "enable_2fa" in data else data.get("enable2fa")
        public_schema = get_public_schema_name()

        # 🌟 ১. সরাসরি PUBLIC স্কিমার ভেতরে ঢুকে মূল Users টেবিলে পাসওয়ার্ড হ্যাশ করে সেভ করা
        with schema_context(public_schema):
            targets = set()

            # টোকেন থেকে আইডি
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                try:
                    from rest_framework_simplejwt.tokens import AccessToken
                    token_str = auth_header.split(' ')[1]
                    token = AccessToken(token_str)
                    u = User.objects.filter(id=token['user_id']).first()
                    if u:
                        targets.add(u)
                except Exception:
                    pass

            # সেশন ইউজার
            if request.user and getattr(request.user, 'is_authenticated', False):
                targets.add(request.user)

            # ইমেইল দিয়ে ফিল্টার (yeakub@gmail.com বা রিকোয়েস্টের ইমেইল)
            candidate_emails = [e for e in [email_from_req, 'yeakub@gmail.com'] if e]
            for em in candidate_emails:
                for u in User.objects.filter(email__iexact=em):
                    targets.add(u)

            # ফলব্যাক সুপারইউজার
            if not targets:
                for u in User.objects.filter(is_superuser=True):
                    targets.add(u)

            if not targets:
                return Response({"detail": "ইউজার অ্যাকাউন্ট খুঁজে পাওয়া যায়নি।"}, status=status.HTTP_404_NOT_FOUND)

            # পাবলিক স্কিমায় পাসওয়ার্ড হ্যাশ করে সেভ
            for u in targets:
                u.set_password(new_password)
                u.is_active = True
                if enable_2fa is not None and hasattr(u, 'two_factor_enabled'):
                    u.two_factor_enabled = bool(enable_2fa)
                u.save()

        # 🌟 ২. বর্তমান টেন্যান্ট স্কিমাতেও যদি কোনো রেকর্ড থাকে, তাও আপডেট রাখা
        try:
            from django.db import connection
            if connection.schema_name and connection.schema_name != public_schema:
                for em in [email_from_req, 'yeakub@gmail.com']:
                    if em:
                        for tu in User.objects.filter(email__iexact=em):
                            tu.set_password(new_password)
                            tu.is_active = True
                            tu.save()
        except Exception:
            pass

        return Response({
            "message": "পাসওয়ার্ড সফলভাবে পরিবর্তন করা হয়েছে! নতুন পাসওয়ার্ড দিয়ে আবার লগইন করুন।"
        }, status=status.HTTP_200_OK)

class MerchantSubscriptionView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        now = timezone.now()
        expiry_date = (now + timedelta(days=28)).strftime("%d %B, %Y")
        
        return Response({
            "plan_name": "Pro Merchant Plan",
            "price": "৳2,499 / mas",
            "status": "Active",
            "days_left": 28,
            "expiry_date": expiry_date,
            "max_products": 500,
            "custom_domain_enabled": True,
            "plans_available": [
                {"id": "starter", "name": "Starter Plan", "price": "৳999/mo", "products": "100 Products"},
                {"id": "pro", "name": "Pro Merchant", "price": "৳2,499/mo", "products": "500 Products (Current)"},
                {"id": "enterprise", "name": "Enterprise Unlimited", "price": "৳4,999/mo", "products": "Unlimited Products"},
            ]
        })

    def post(self, request):
        selected_plan = request.data.get("plan_id")
        return Response({
            "message": f"{selected_plan.upper()} plane renewal request shofolbhabe submit hoyeche!",
            "status": "Active"
        }, status=status.HTTP_200_OK)


class SuperAdminNotificationsView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response([
            {
                "id": 1,
                "title": "System maintenance notice",
                "message": "Agami robibar raat 2:00 theke 3:00 porjonto server optimization cholbe. Storefront shochol thakbe.",
                "type": "warning",
                "created_at": "Today, 11:30 AM",
                "is_read": False
            },
            {
                "id": 2,
                "title": "Notun payment gateway",
                "message": "Apnar store-er jonno Nagad & Rocket gateway auto-configure kora hoyeche.",
                "type": "success",
                "created_at": "Yesterday",
                "is_read": True
            }
        ])


class ThemeMarketplaceView(APIView):
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def get_tenant(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant and self.request.user and self.request.user.is_authenticated:
            tenant = getattr(self.request.user, 'tenant', None)
        if not tenant:
            host = self.request.get_host().split(':')[0]
            subdomain = host.split('.')[0]
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.filter(subdomain__iexact=subdomain).first()
        return tenant or Tenant.objects.first()

    def get(self, request):
        tenant = self.get_tenant()
        settings = StoreSettings.objects.filter(tenant=tenant).first() or StoreSettings.objects.first()
        
        current_theme = getattr(settings, 'theme', 'default') if settings else 'default'
        if not current_theme:
            current_theme = 'default'
            
        theme_config = getattr(settings, 'theme_config', {}) or {}
        if not isinstance(theme_config, dict):
            theme_config = {}
            
        purchased = theme_config.get('purchased_themes', ['default'])
        if 'default' not in purchased:
            purchased.append('default')

        available_themes = [
            {
                'id': 1,
                'key': 'default',
                'name': 'Modern Clean E-Commerce',
                'tagline': 'Default grocery & fashion high-converting layout',
                'price': 0.00,
                'is_free': True,
                'preview_image_url': 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=600',
                'is_purchased': True,
                'is_active': (current_theme == 'default'),
            },
            {
                'id': 2,
                'key': 'classified_soft',
                'name': 'Soft 3D Claymorphism',
                'tagline': 'Clean neo-clay classified layout with floating 3D elements',
                'price': 1499.00,
                'is_free': False,
                'preview_image_url': 'https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=600',
                'is_purchased': ('classified_soft' in purchased),
                'is_active': (current_theme == 'classified_soft'),
            },
            {
                'id': 3,
                'key': 'neon_studio',
                'name': 'Cyber Neon Dark Studio',
                'tagline': 'Ultra-modern dark aesthetic with neon glow and glass cards',
                'price': 2499.00,
                'is_free': False,
                'preview_image_url': 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=600',
                'is_purchased': ('neon_studio' in purchased),
                'is_active': (current_theme == 'neon_studio'),
            },
        ]
        return Response(available_themes, status=status.HTTP_200_OK)


class ThemeActionView(APIView):
    authentication_classes = [SafeJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def get_tenant(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant and self.request.user and self.request.user.is_authenticated:
            tenant = getattr(self.request.user, 'tenant', None)
        if not tenant:
            host = self.request.get_host().split(':')[0]
            subdomain = host.split('.')[0]
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.filter(subdomain__iexact=subdomain).first()
        return tenant or Tenant.objects.first()

    def post(self, request):
        action = request.data.get('action')
        theme_key = request.data.get('theme_key')

        if not theme_key:
            return Response({'detail': 'theme_key prodan kora oboshok.'}, status=status.HTTP_400_BAD_REQUEST)

        tenant = self.get_tenant()
        settings = StoreSettings.objects.filter(tenant=tenant).first() or StoreSettings.objects.first()

        if not settings:
            settings = StoreSettings.objects.create(
                tenant=tenant,
                store_name=getattr(tenant, 'name', 'My Store') if tenant else 'My Store'
            )

        theme_config = getattr(settings, 'theme_config', {}) or {}
        if not isinstance(theme_config, dict):
            theme_config = {}

        purchased = theme_config.get('purchased_themes', ['default'])

        if action == 'buy':
            if theme_key not in purchased:
                purchased.append(theme_key)
            theme_config['purchased_themes'] = purchased
            settings.theme_config = theme_config
            settings.theme = theme_key
            settings.save()
            return Response({'message': f'"{theme_key}" theme-ti shofolbhabe active kora hoyeche!'}, status=status.HTTP_200_OK)

        elif action == 'activate':
            if theme_key != 'default' and theme_key not in purchased:
                return Response({'detail': 'Ei theme-ti use korte age kroy korte hobe.'}, status=status.HTTP_400_BAD_REQUEST)

            settings.theme = theme_key
            settings.save(update_fields=['theme'])
            return Response({'message': f'"{theme_key}" theme-ti store-e active kora hoyeche!'}, status=status.HTTP_200_OK)

        return Response({'detail': 'Sothik action prodan korun.'}, status=status.HTTP_400_BAD_REQUEST)