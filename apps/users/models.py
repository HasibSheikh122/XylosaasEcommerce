from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):
    """Custom manager where email is the unique identifier for authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'super_admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('store_owner', 'Store Owner'),
        ('staff', 'Staff'),
        ('customer', 'Customer'),
    ]
    
    # ইউজারনেম ফিল্ডটি পুরোপুরি ডিজেবল বা নাল করে দেওয়া হচ্ছে
    username = None 
    email = models.EmailField(unique=True) # ইমেইল ইউনিক করা হলো
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, blank=True)
    
    # For multi-tenant
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Profile
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Settings
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    
    # Metadata
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_device = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 🌟 জ্যাঙ্গোকে ইমেইল দিয়ে লগইন করতে বাধ্য করার কনফিগারেশন
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] #createsuperuser করার সময় ইমেইল ছাড়া আর কিছু লাগবে না

    objects = CustomUserManager() # কাস্টম ম্যানেজার অ্যাসাইন করা হলো

    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return self.email