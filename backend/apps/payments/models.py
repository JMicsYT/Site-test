from django.db import models

from apps.orders.models import Order


class PaymentNotification(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payment_notifications",
        verbose_name="Заказ",
    )
    raw_data = models.JSONField("Сырые данные")
    processed = models.BooleanField("Обработано", default=False)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Платёжное уведомление"
        verbose_name_plural = "Платёжные уведомления"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Уведомление для заказа #{self.order_id}"

