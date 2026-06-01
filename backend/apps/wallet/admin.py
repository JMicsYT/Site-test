from django.contrib import admin

from .models import Wallet, WalletTransaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ["user", "balance", "currency", "updated_at"]
    search_fields = ["user__email"]
    autocomplete_fields = ["user"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ["wallet", "tx_type", "amount", "balance_after", "order", "created_at"]
    list_filter = ["tx_type", "created_at"]
    search_fields = ["wallet__user__email", "description"]
    autocomplete_fields = ["wallet", "order"]
    readonly_fields = ["created_at"]
