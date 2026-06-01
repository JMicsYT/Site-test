from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from apps.core.crypto import decrypt_value, encrypt_value, is_encrypted


class Category(models.Model):
    name = models.CharField("Название", max_length=255)
    slug = models.SlugField("Слаг", max_length=255, unique=True, db_index=True)
    description = models.TextField("Описание", blank=True)
    icon = models.CharField(
        "Иконка (emoji или короткий код)",
        max_length=8,
        blank=True,
        help_text="Например 🎮 или буква",
    )
    color = models.CharField(
        "Цвет (HEX)",
        max_length=9,
        blank=True,
        default="#4f46e5",
        help_text="Цвет акцента, напр. #4f46e5",
    )
    image_url = models.URLField(
        "URL изображения", max_length=500, blank=True,
        help_text="Опционально: изображение-обложка категории",
    )
    featured = models.BooleanField("На главной", default=False, db_index=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0, db_index=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Менеджер по умолчанию возвращает только живые записи."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class SoftDeleteAllManager(models.Manager):
    """all_objects — без фильтра, видно и удалённые (для админки и аудита)."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class Product(models.Model):
    class ProductType(models.TextChoices):
        GAME = "game", "Игра"
        SOFTWARE = "software", "ПО"
        COURSE = "course", "Курс"
        MEDIA = "media", "Медиа"
        ASSET = "asset", "Asset"

    class LicenseType(models.TextChoices):
        PERPETUAL = "perpetual", "Бессрочная"
        SUBSCRIPTION = "subscription", "Подписка"

    class Purpose(models.TextChoices):
        PERSONAL = "personal", "Личное"
        BUSINESS = "business", "Бизнес"

    class Status(models.TextChoices):
        ACTIVE = "active", "Активен"
        HIDDEN = "hidden", "Скрыт"
        DISABLED = "disabled", "Отключен"

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="Категория",
    )
    name = models.CharField("Название", max_length=255, db_index=True)
    slug = models.SlugField("Слаг", max_length=255, unique=True, db_index=True)
    short_description = models.CharField("Краткое описание", max_length=512)
    description = models.TextField("Полное описание")
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2, db_index=True)
    product_type = models.CharField(
        "Тип товара",
        max_length=32,
        choices=ProductType.choices,
        db_index=True,
    )
    license_type = models.CharField(
        "Тип лицензии",
        max_length=32,
        choices=LicenseType.choices,
        db_index=True,
    )
    purpose = models.CharField(
        "Назначение",
        max_length=16,
        choices=Purpose.choices,
        db_index=True,
    )
    status = models.CharField(
        "Статус",
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    is_featured = models.BooleanField("Рекомендуемый", default=False, db_index=True)
    discount_price = models.DecimalField(
        "Цена со скидкой",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Если задана — отображается как цена, а старая зачёркивается",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    # ===== Soft-delete =====
    is_deleted = models.BooleanField("Удалён (soft)", default=False, db_index=True)
    deleted_at = models.DateTimeField("Дата удаления", null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteAllManager()

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def soft_delete(self):
        """Помечает товар удалённым без реальной потери данных."""
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.status = self.Status.DISABLED
            self.save(update_fields=["is_deleted", "deleted_at", "status"])

    def restore(self):
        """Восстановление soft-deleted товара."""
        if self.is_deleted:
            self.is_deleted = False
            self.deleted_at = None
            self.save(update_fields=["is_deleted", "deleted_at"])

    def get_first_image_url(self):
        """URL первого изображения товара для превью в каталоге."""
        first = (
            self.media.filter(media_type="image")
            .order_by("sort_order", "id")
            .first()
        )
        return first.url if first else None

    @property
    def final_price(self):
        return self.discount_price if self.discount_price else self.price

    @property
    def has_discount(self) -> bool:
        return bool(self.discount_price and self.discount_price < self.price)

    @property
    def discount_percent(self) -> int:
        if not self.has_discount:
            return 0
        try:
            return int(round((1 - float(self.discount_price) / float(self.price)) * 100))
        except (ZeroDivisionError, TypeError):
            return 0

    @property
    def is_new(self) -> bool:
        from django.utils import timezone
        from datetime import timedelta
        return self.created_at >= timezone.now() - timedelta(days=14)

    @property
    def avg_rating(self) -> float:
        """Средний рейтинг по опубликованным отзывам. 0, если отзывов нет."""
        # Если уже посчитано аннотацией в QuerySet (поле _avg_rating), используем.
        cached = self.__dict__.get("_avg_rating")
        if cached is not None:
            try:
                return float(cached)
            except (TypeError, ValueError):
                return 0.0
        try:
            from django.db.models import Avg
            val = self.reviews.filter(status=Review.Status.PUBLISHED).aggregate(
                a=Avg("rating")
            )["a"]
            return float(val) if val is not None else 0.0
        except Exception:
            return 0.0

    @property
    def reviews_count(self) -> int:
        """Количество опубликованных отзывов."""
        cached = self.__dict__.get("_reviews_count")
        if cached is not None:
            try:
                return int(cached)
            except (TypeError, ValueError):
                return 0
        try:
            return self.reviews.filter(status=Review.Status.PUBLISHED).count()
        except Exception:
            return 0


class ProductMedia(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Изображение"
        VIDEO = "video", "Видео"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="media",
        verbose_name="Товар",
    )
    media_type = models.CharField(
        "Тип",
        max_length=16,
        choices=MediaType.choices,
    )
    url = models.URLField("URL", max_length=500)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Медиа товара"
        verbose_name_plural = "Медиа товаров"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"{self.product} #{self.pk}"


class DigitalItem(models.Model):
    class ItemType(models.TextChoices):
        FILE = "file", "Файл"
        KEY = "key", "Ключ"
        LINK = "link", "Ссылка"
        ACCESS_CODE = "access_code", "Код доступа"

    class ItemStatus(models.TextChoices):
        AVAILABLE = "available", "Доступен"
        RESERVED = "reserved", "Зарезервирован"
        SOLD = "sold", "Продан"

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="digital_items",
        verbose_name="Товар",
    )
    item_type = models.CharField("Тип", max_length=32, choices=ItemType.choices)
    # Значение в БД ВСЕГДА хранится в зашифрованном виде (enc:v1:...),
    # если задан FIELD_ENCRYPTION_KEY. Доступ — через свойство .plain_value.
    value = models.TextField("Значение (зашифровано)")
    max_activations = models.PositiveIntegerField(
        "Количество активаций", default=1, help_text="0 — без ограничений"
    )
    status = models.CharField(
        "Статус",
        max_length=16,
        choices=ItemStatus.choices,
        default=ItemStatus.AVAILABLE,
        db_index=True,
    )

    class Meta:
        verbose_name = "Цифровой элемент"
        verbose_name_plural = "Цифровые элементы"
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.product} [{self.item_type}] {self.status}"

    # ===== Прозрачное шифрование =====
    @property
    def plain_value(self) -> str:
        """Расшифрованное значение для передачи пользователю. Никогда не логировать!"""
        return decrypt_value(self.value or "")

    @plain_value.setter
    def plain_value(self, new_value: str) -> None:
        self.value = encrypt_value(new_value or "")

    def save(self, *args, **kwargs):
        # Автоматически шифруем значение при сохранении, если ещё не зашифровано
        if self.value and not is_encrypted(self.value):
            self.value = encrypt_value(self.value)
        super().save(*args, **kwargs)

    @property
    def is_encrypted_at_rest(self) -> bool:
        return is_encrypted(self.value or "")


class Review(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "На модерации"
        PUBLISHED = "published", "Опубликован"
        HIDDEN = "hidden", "Скрыт"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Товар",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
        verbose_name="Пользователь",
    )
    rating = models.PositiveSmallIntegerField("Рейтинг", default=5)
    text = models.TextField("Отзыв", blank=True)
    status = models.CharField(
        "Статус",
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.product} ({self.rating})"

