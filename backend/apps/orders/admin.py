from django.contrib import admin
from .models import Order, OrderItem, UserDigitalAccess


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "status", "amount", "currency", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__email", "transaction_id"]
    inlines = [OrderItemInline]


@admin.register(UserDigitalAccess)
class UserDigitalAccessAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "purchased_at"]
    list_filter = ["purchased_at"]
