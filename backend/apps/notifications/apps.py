from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    verbose_name = "Уведомления"

    def ready(self):
        # Подключаем сигналы, отправляющие push + пишущие в БД.
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
