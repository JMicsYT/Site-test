from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "first_name", "last_name", "role", "is_active", "email_verified", "date_joined"]
    list_filter = ["role", "is_active", "email_verified"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["-date_joined"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Профиль", {"fields": (
            "first_name", "last_name", "avatar", "bio",
            "phone", "telegram", "birth_date",
            "country", "city", "address", "newsletter",
        )}),
        ("Права", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
        ("Верификация", {"fields": ("email_verified",)}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
