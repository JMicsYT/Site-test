from django.conf import settings
from django.db import models


class SecurityEvent(models.Model):
    """
    Аудит-лог действий, влияющих на безопасность.
    Пишется из apps.core.audit.log_event() — помощника с единой точкой входа.
    """

    EVENT_TYPES = [
        ("login_success", "Успешный вход"),
        ("login_failed", "Неуспешный вход"),
        ("logout", "Выход"),
        ("register", "Регистрация"),
        ("password_change", "Смена пароля"),
        ("password_reset_request", "Запрос сброса пароля"),
        ("password_reset_done", "Сброс пароля выполнен"),
        ("email_verified", "Email подтверждён"),
        ("twofa_enabled", "2FA включена"),
        ("twofa_disabled", "2FA отключена"),
        ("twofa_failed", "Неуспешный код 2FA"),
        ("account_locked", "Аккаунт заблокирован"),
        ("account_unlocked", "Аккаунт разблокирован"),
        ("order_paid", "Оплата заказа"),
        ("order_cancelled", "Отмена заказа"),
        ("payment_callback_ok", "Платёжный callback (ok)"),
        ("payment_callback_fail", "Платёжный callback (ошибка/подпись)"),
        ("digital_download", "Скачивание/просмотр цифрового товара"),
        ("admin_action", "Действие администратора"),
        ("suspicious_activity", "Подозрительная активность"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_events",
        verbose_name="Пользователь",
    )
    event_type = models.CharField(
        "Тип события", max_length=64, choices=EVENT_TYPES, db_index=True
    )
    description = models.TextField("Описание", blank=True)
    ip_address = models.GenericIPAddressField("IP", null=True, blank=True)
    user_agent = models.CharField("User-Agent", max_length=512, blank=True)
    meta = models.JSONField("Метаданные", blank=True, default=dict)
    created_at = models.DateTimeField("Время", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Событие безопасности"
        verbose_name_plural = "События безопасности"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} ({self.created_at})"


class DownloadAudit(models.Model):
    """
    Журнал скачиваний/просмотров цифрового товара (кто, что, когда, откуда).
    Нужен для расследования инцидентов и отчётности.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="download_audits",
        verbose_name="Пользователь",
    )
    access_id = models.PositiveIntegerField("ID UserDigitalAccess", db_index=True)
    product_id = models.PositiveIntegerField("ID товара", db_index=True)
    digital_item_id = models.PositiveIntegerField(
        "ID DigitalItem", null=True, blank=True
    )
    token_jti = models.CharField(
        "JTI подписанной ссылки", max_length=64, blank=True, db_index=True
    )
    ip_address = models.GenericIPAddressField("IP", null=True, blank=True)
    user_agent = models.CharField("User-Agent", max_length=512, blank=True)
    success = models.BooleanField("Успех", default=True)
    reason = models.CharField("Причина отказа", max_length=128, blank=True)
    created_at = models.DateTimeField("Время", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Событие скачивания"
        verbose_name_plural = "Журнал скачиваний"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["product_id", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"download user={self.user_id} product={self.product_id} ok={self.success}"


class SupportTicket(models.Model):
    """Обращение в поддержку: привязано к пользователю, хранится до отметки «завершён» админом."""

    class Status(models.TextChoices):
        OPEN = "open", "Открыт"
        COMPLETED = "completed", "Завершён"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_tickets",
        verbose_name="Пользователь",
    )
    status = models.CharField(
        "Статус",
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Обращение в поддержку"
        verbose_name_plural = "Обращения в поддержку"
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"#{self.pk} — {self.user.email} ({self.get_status_display()})"


class SupportMessage(models.Model):
    """Сообщение в обращении: от пользователя или от сотрудника."""

    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Обращение",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_messages",
        verbose_name="Автор",
    )
    body = models.TextField("Текст")
    created_at = models.DateTimeField("Создано", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Сообщение поддержки"
        verbose_name_plural = "Сообщения поддержки"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.author.email}: {self.body[:50]}..."

    @property
    def is_staff_reply(self) -> bool:
        return self.author.is_staff


class SiteSetting(models.Model):
    """Ключ-значение для общих настроек (платёжный провайдер, email, текстовые блоки)."""
    key = models.CharField("Ключ", max_length=128, unique=True, db_index=True)
    value = models.TextField("Значение", blank=True)

    class Meta:
        verbose_name = "Настройка сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self) -> str:
        return self.key

    @classmethod
    def get(cls, key: str, default: str = "") -> str:
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key: str, value: str) -> None:
        obj, _ = cls.objects.get_or_create(key=key, defaults={"value": value})
        obj.value = value
        obj.save()

