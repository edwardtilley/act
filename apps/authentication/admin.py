from django.contrib import admin
from .models import UserProfile

# User is already registered by django.contrib.auth.admin


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'certification')
    list_filter = ('role', 'certification')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
