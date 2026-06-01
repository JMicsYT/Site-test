from django.conf import settings
from django.db import models


class Notification(models.Model):
    """Внутрисайтовое уведомление пользователю."""

    class Type(models.TextChoices):
        ORDER_PAID = "order_paid", "Заказ оплачен"
        ORDER_FAILED = "order_failed", "Ошибка оплаты"
        SUPPORT_REPLY = "support_reply", "Ответ поддержки"
        REVIEW_APPROVED = "review_approved", "Отзыв опубликован"
        WALLET_DEPOSIT = "wallet_deposit", "Пополнение кошелька"
        REFERRAL_BONUS = "referral_bonus", "Реферальный бонус"
        SYSTEM = "system", "Системное"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Пользователь",
    )
    type = models.CharField(
        "Тип", max_length=32, choices=Type.choices, default=Type.SYSTEM, db_index=True
    )
    title = models.CharField("Заголовок", max_length=255)
    body = models.TextField("Текст", blank=True)
    url = models.CharField("Ссылка", max_length=500, blank=True)
    is_read = models.BooleanField("Прочитано", default=False, db_index=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"[{self.type}] {self.title} → {self.user_id}"

    def to_dict(self) -> dict:
        return {
            "id": self.pk,
            "type": self.type,
            "title": self.title,
            "body": self.body,
            "url": self.url,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
        }
