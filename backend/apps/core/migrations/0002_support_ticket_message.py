# Generated for SupportTicket and SupportMessage

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SupportTicket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("open", "Открыт"), ("completed", "Завершён")], db_index=True, default="open", max_length=16, verbose_name="Статус")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Создан")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлён")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="support_tickets", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
            ],
            options={
                "verbose_name": "Обращение в поддержку",
                "verbose_name_plural": "Обращения в поддержку",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="SupportMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField(verbose_name="Текст")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Создано")),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="support_messages", to=settings.AUTH_USER_MODEL, verbose_name="Автор")),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="core.supportticket", verbose_name="Обращение")),
            ],
            options={
                "verbose_name": "Сообщение поддержки",
                "verbose_name_plural": "Сообщения поддержки",
                "ordering": ["created_at"],
            },
        ),
    ]
