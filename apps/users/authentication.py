from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.settings import api_settings
from django_tenants.utils import schema_context, get_public_schema_name
from django.contrib.auth import get_user_model

User = get_user_model()


class TenantJWTAuthentication(JWTAuthentication):
    """
    মাল্টি-টেন্যান্ট আর্কিটেকচারে যে সাবডোমেন থেকেই কল আসুক না কেন,
    এটি টোকেন থেকে আইডি পড়ে সরাসরি 'public' স্কিমা থেকে ইউজার লোড করে।
    """
    def get_user(self, validated_token):
        # ১. টোকেন পে-লোড থেকে যেকোনো ফরমেটের আইডি (user_id, id, বা sub) নিরাপদে রিড করা
        user_id = (
            validated_token.get(api_settings.USER_ID_CLAIM)
            or validated_token.get('user_id')
            or validated_token.get('id')
            or validated_token.get('sub')
        )

        if user_id is None:
            raise InvalidToken("Token contained no recognizable user identification")

        # ২. স্কিমা আইসোলেশন হ্যান্ডেল করে পাবলিক স্কিমার টেবিলে কুয়েরি করা
        public_schema = get_public_schema_name()
        with schema_context(public_schema):
            try:
                user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
            except User.DoesNotExist:
                # ফলব্যাক: আইডি না পেলে টোকেনের ইমেইল দিয়ে খোঁজা
                email = validated_token.get('email')
                if email:
                    try:
                        user = User.objects.get(email=email)
                    except User.DoesNotExist:
                        raise AuthenticationFailed("User not found", code="user_not_found")
                else:
                    raise AuthenticationFailed("User not found", code="user_not_found")

            if not user.is_active:
                raise AuthenticationFailed("User is inactive", code="user_inactive")

            return user