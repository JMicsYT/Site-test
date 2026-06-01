from django.contrib import admin
from .models import PaymentNotification


@admin.register(PaymentNotification)
class PaymentNotificationAdmin(admin.ModelAdmin):
    list_display = ["order", "processed", "created_at"]
    list_filter = ["processed"]
