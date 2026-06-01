from django.contrib import admin
from .models import Category, DigitalItem, Product, ProductMedia, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "icon", "featured", "sort_order"]
    list_filter = ["featured"]
    search_fields = ["name"]
    fieldsets = (
        (None, {"fields": ("name", "slug", "description", "sort_order")}),
        ("Оформление", {"fields": ("icon", "color", "image_url", "featured")}),
    )


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 0


class DigitalItemInline(admin.TabularInline):
    model = DigitalItem
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "discount_price", "product_type", "status", "is_featured", "created_at"]
    list_filter = ["status", "product_type", "category", "is_featured"]
    list_editable = ["is_featured"]
    search_fields = ["name", "short_description"]
    inlines = [ProductMediaInline, DigitalItemInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "rating", "created_at"]
    list_filter = ["rating"]


@admin.register(DigitalItem)
class DigitalItemAdmin(admin.ModelAdmin):
    """
    Администрирование цифровых ключей/кодов.
    Значение НЕ показываем в списке — храним зашифрованным.
    На форме отображаем «как есть» (зашифрованный текст); чтобы ввести новое
    значение — поле plain_value (write-only).
    """
    list_display = ["product", "item_type", "status", "encrypted_short"]
    list_filter = ["status", "item_type"]
    readonly_fields = ["encrypted_status"]
    fields = ["product", "item_type", "status", "max_activations", "value", "encrypted_status"]

    @admin.display(description="Значение (зашифровано)")
    def encrypted_short(self, obj):
        if not obj.value:
            return "—"
        prefix = "🔒 " if obj.is_encrypted_at_rest else "⚠ "
        return prefix + (obj.value[:18] + "…" if len(obj.value) > 18 else obj.value)

    @admin.display(description="Шифрование")
    def encrypted_status(self, obj):
        if obj.is_encrypted_at_rest:
            return "🔒 Зашифровано (Fernet)"
        return "⚠ Хранится в открытом виде (настройте FIELD_ENCRYPTION_KEY)"


@admin.register(ProductMedia)
class ProductMediaAdmin(admin.ModelAdmin):
    list_display = ["product", "media_type", "sort_order", "url"]
