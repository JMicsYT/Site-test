from decimal import Decimal

from django.conf import settings
from django.db import models


class Wallet(models.Model):
    """Внутренний баланс пользователя (бонусы, рефералка, возвраты)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet",
        verbose_name="Пользователь",
    )
    balance = models.DecimalField(
        "Баланс", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    currency = models.CharField("Валюта", max_length=8, default="RUB")
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Кошелёк"
        verbose_name_plural = "Кошельки"

    def __str__(self) -> str:
        return f"{self.user_id}: {self.balance} {self.currency}"


class WalletTransaction(models.Model):
    """Запись о движении средств в кошельке пользователя."""

    class TxType(models.TextChoices):
        DEPOSIT = "deposit", "Пополнение"
        WITHDRAW = "withdraw", "Списание"
        REFUND = "refund", "Возврат"
        BONUS = "bonus", "Бонус"
        REFERRAL = "referral", "Реферальное вознаграждение"

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Кошелёк",
    )
    tx_type = models.CharField(
        "Тип", max_length=16, choices=TxType.choices, db_index=True
    )
    amount = models.DecimalField(
        "Сумма",
        max_digits=12,
        decimal_places=2,
        help_text="Положительное — приход, отрицательное — списание",
    )
    balance_after = models.DecimalField(
        "Остаток после операции", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="wallet_transactions",
        verbose_name="Заказ",
    )
    description = models.CharField("Описание", max_length=255, blank=True)
    meta = models.JSONField("Метаданные", default=dict, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Операция кошелька"
        verbose_name_plural = "Операции кошелька"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["wallet", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.wallet_id} {self.tx_type} {self.amount}"


def get_or_create_wallet(user) -> Wallet:
    """Удобный хелпер: гарантирует наличие кошелька у пользователя."""
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet
