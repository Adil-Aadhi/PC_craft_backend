from django.contrib import admin
from .models import User, UserProfile, WorkerProfile

# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'role', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('role', 'is_active')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_name')
    search_fields = ('user__username', 'full_name')

@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'kyc_status',
        'availability',
        'rating'
    )
    list_filter = ('kyc_status', 'availability')
    search_fields = ('user__username', 'user__email')
