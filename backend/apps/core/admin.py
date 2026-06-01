from django.contrib import admin
from .models import SecurityEvent, SiteSetting, SupportMessage, SupportTicket


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0
    readonly_fields = ["author", "body", "created_at"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "status", "created_at", "updated_at"]
    list_filter = ["status"]
    search_fields = ["user__email"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [SupportMessageInline]


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ["event_type", "user", "ip_address", "created_at"]
    list_filter = ["event_type"]
    search_fields = ["description"]
    readonly_fields = ["created_at"]


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ["key", "value"]
    search_fields = ["key"]
