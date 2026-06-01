from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    """Промокод со скидкой (процент или фиксированная сумма)."""

    class DiscountType(models.TextChoices):
        PERCENT = "percent", "Процент"
        FIXED = "fixed", "Фиксированная сумма"

    code = models.CharField("Код", max_length=64, unique=True, db_index=True)
    description = models.CharField("Описание", max_length=255, blank=True)
    discount_type = models.CharField(
        "Тип скидки",
        max_length=16,
        choices=DiscountType.choices,
        default=DiscountType.PERCENT,
    )
    value = models.DecimalField(
        "Значение скидки",
        max_digits=10,
        decimal_places=2,
        help_text="Для процента — число 1..100. Для фиксированной — сумма в RUB.",
    )
    min_order_amount = models.DecimalField(
        "Мин. сумма заказа", max_digits=10, decimal_places=2, default=Decimal("0")
    )
    max_uses = models.PositiveIntegerField(
        "Лимит активаций", default=0,
        help_text="0 — без ограничений",
    )
    uses_count = models.PositiveIntegerField("Активаций", default=0)
    once_per_user = models.BooleanField("Один раз на пользователя", default=True)
    valid_from = models.DateTimeField("Действует с", default=timezone.now)
    valid_until = models.DateTimeField("Действует до", null=True, blank=True)
    is_active = models.BooleanField("Активен", default=True, db_index=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code

    def is_valid(self) -> bool:
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and self.valid_from > now:
            return False
        if self.valid_until and self.valid_until < now:
            return False
        if self.max_uses and self.uses_count >= self.max_uses:
            return False
        return True

    def compute_discount(self, amount: Decimal) -> Decimal:
        """Сколько рублей снимет этот промокод с суммы amount."""
        if amount < self.min_order_amount:
            return Decimal("0")
        if self.discount_type == self.DiscountType.PERCENT:
            discount = (amount * self.value / Decimal("100")).quantize(Decimal("0.01"))
        else:
            discount = Decimal(self.value)
        if discount > amount:
            discount = amount
        return discount.quantize(Decimal("0.01"))


class CouponUsage(models.Model):
    """Факт использования промокода конкретным пользователем в конкретном заказе."""

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name="usages",
        verbose_name="Промокод",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="coupon_usages",
        verbose_name="Пользователь",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="coupon_usages",
        verbose_name="Заказ",
    )
    discount_amount = models.DecimalField(
        "Сумма скидки", max_digits=10, decimal_places=2, default=Decimal("0")
    )
    used_at = models.DateTimeField("Использован", auto_now_add=True)

    class Meta:
        verbose_name = "Использование промокода"
        verbose_name_plural = "Использования промокодов"
        ordering = ["-used_at"]
        indexes = [
            models.Index(fields=["coupon", "user"]),
        ]

    def __str__(self) -> str:
        return f"{self.coupon_id} / {self.user_id}"
