from django.db import models
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin
from .managers import UserManager


# Create your models here.

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('worker', 'Worker'),
        ('admin', 'Admin'),
    )

    AUTH_PROVIDERS = (
        ('email', 'Email'),
        ('google', 'Google'),
    )

    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

    auth_provider = models.CharField(
        max_length=20,
        choices=AUTH_PROVIDERS,
        default='email'
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    last_login = models.DateField(null=True, blank=True)
    date_joined = models.DateField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
    
class UserProfile(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')

    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, blank=True,null=True)
    date_of_birth = models.DateField( blank=True,null=True)

    profile_image = models.URLField(blank=True, null=True)
    profile_image_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.full_name

class WorkerProfile(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='worker_profile')

    description = models.CharField(max_length=255,blank=True,null=True)
    skills = models.TextField(blank=True,null=True)
    experience_years = models.BigIntegerField(blank=True,null=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)
    availability = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    profile_image = models.URLField(blank=True, null=True)
    profile_image_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    kyc_status = models.CharField(
    choices=[('pending','Pending'), ('approved','Approved'), ('rejected','Rejected')],
    default='pending'
    )
    banner_image = models.URLField(blank=True, null=True)
    banner_image_id = models.CharField(max_length=255, blank=True, null=True)
  
    def __str__(self):
        return self.user.email




