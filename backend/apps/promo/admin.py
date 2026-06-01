from django.contrib import admin

from .models import Coupon, CouponUsage


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        "code", "discount_type", "value",
        "uses_count", "max_uses",
        "is_active", "valid_from", "valid_until",
    ]
    list_filter = ["discount_type", "is_active"]
    search_fields = ["code", "description"]
    readonly_fields = ["uses_count", "created_at"]


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ["coupon", "user", "order", "discount_amount", "used_at"]
    list_filter = ["used_at"]
    search_fields = ["coupon__code", "user__email"]
    autocomplete_fields = ["coupon", "user", "order"]
