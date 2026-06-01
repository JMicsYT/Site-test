# Generated manually for SecurityEvent and SiteSetting

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SecurityEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(choices=[("login_failed", "Неуспешный логин"), ("suspicious_activity", "Подозрительная активность"), ("payment_error", "Ошибка оплаты"), ("admin_action", "Действие администратора")], max_length=64, verbose_name="Тип события")),
                ("description", models.TextField(verbose_name="Описание")),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True, verbose_name="IP")),
                ("user_agent", models.CharField(blank=True, max_length=512, verbose_name="User-Agent")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Время")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="security_events", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
            ],
            options={
                "verbose_name": "Событие безопасности",
                "verbose_name_plural": "События безопасности",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="SiteSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(db_index=True, max_length=128, unique=True, verbose_name="Ключ")),
                ("value", models.TextField(blank=True, verbose_name="Значение")),
            ],
            options={
                "verbose_name": "Настройка сайта",
                "verbose_name_plural": "Настройки сайта",
            },
        ),
    ]
