from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.catalog.models import DigitalItem, Product


class Order(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Создан"
        PENDING = "pending_payment", "Ожидание оплаты"
        PAID = "paid", "Оплачен"
        FAILED = "failed", "Неуспешен"
        CANCELLED = "cancelled", "Отменён"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Пользователь",
    )
    status = models.CharField(
        "Статус",
        max_length=32,
        choices=Status.choices,
        default=Status.CREATED,
        db_index=True,
    )
    amount = models.DecimalField("Сумма", max_digits=10, decimal_places=2)
    currency = models.CharField("Валюта", max_length=8, default="RUB")
    transaction_id = models.CharField(
        "ID транзакции", max_length=128, blank=True, db_index=True
    )
    meta = models.JSONField("Метаданные", blank=True, default=dict)
    created_at = models.DateTimeField("Создан", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    # ===== Soft-delete =====
    is_deleted = models.BooleanField("Удалён (soft)", default=False, db_index=True)
    deleted_at = models.DateTimeField("Дата удаления", null=True, blank=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Заказ #{self.pk} ({self.status})"

    def soft_delete(self):
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self):
        if self.is_deleted:
            self.is_deleted = False
            self.deleted_at = None
            self.save(update_fields=["is_deleted", "deleted_at"])


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Заказ",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Товар",
    )
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("Количество", default=1)
    digital_item = models.ForeignKey(
        DigitalItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name="Цифровой элемент",
    )

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self) -> str:
        return f"{self.product} x{self.quantity}"


class OrderEvent(models.Model):
    """Событие в жизненном цикле заказа: смена статуса, платёж, выдача, возврат."""

    class EventType(models.TextChoices):
        CREATED = "created", "Создан"
        PENDING = "pending_payment", "Ожидание оплаты"
        PAID = "paid", "Оплачен"
        FAILED = "failed", "Ошибка оплаты"
        CANCELLED = "cancelled", "Отменён"
        FULFILLED = "fulfilled", "Товары выданы"
        REFUND = "refund", "Возврат"
        NOTE = "note", "Комментарий"

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Заказ",
    )
    event_type = models.CharField(
        "Тип события", max_length=32, choices=EventType.choices, db_index=True,
    )
    description = models.CharField("Описание", max_length=500, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="order_events",
        verbose_name="Автор",
    )
    meta = models.JSONField("Метаданные", default=dict, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Событие заказа"
        verbose_name_plural = "События заказов"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"#{self.order_id} [{self.event_type}]"


class UserDigitalAccess(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="digital_access",
        verbose_name="Пользователь",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="user_access",
        verbose_name="Товар",
    )
    digital_item = models.ForeignKey(
        DigitalItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_access",
        verbose_name="Цифровой элемент",
    )
    purchased_at = models.DateTimeField("Дата покупки", default=timezone.now)
    can_redownload = models.BooleanField(
        "Повторное скачивание", default=True
    )

    class Meta:
        verbose_name = "Доступ пользователя к цифровому товару"
        verbose_name_plural = "Доступы пользователей к цифровым товарам"
        unique_together = ("user", "product", "digital_item")

    def __str__(self) -> str:
        return f"{self.user} → {self.product}"

