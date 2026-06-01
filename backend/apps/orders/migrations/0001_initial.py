# Generated for Order, OrderItem, UserDigitalAccess

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("catalog", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(db_index=True, default="created", max_length=32, verbose_name="Статус")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Сумма")),
                ("currency", models.CharField(default="RUB", max_length=8, verbose_name="Валюта")),
                ("transaction_id", models.CharField(blank=True, db_index=True, max_length=128, verbose_name="ID транзакции")),
                ("meta", models.JSONField(blank=True, default=dict, verbose_name="Метаданные")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Создан")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлён")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="orders", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
            ],
            options={
                "verbose_name": "Заказ",
                "verbose_name_plural": "Заказы",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("price", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Цена")),
                ("quantity", models.PositiveIntegerField(default=1, verbose_name="Количество")),
                ("digital_item", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="order_items", to="catalog.digitalitem", verbose_name="Цифровой элемент")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="orders.order", verbose_name="Заказ")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_items", to="catalog.product", verbose_name="Товар")),
            ],
            options={
                "verbose_name": "Позиция заказа",
                "verbose_name_plural": "Позиции заказа",
            },
        ),
        migrations.CreateModel(
            name="UserDigitalAccess",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("purchased_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Дата покупки")),
                ("can_redownload", models.BooleanField(default=True, verbose_name="Повторное скачивание")),
                ("digital_item", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="user_access", to="catalog.digitalitem", verbose_name="Цифровой элемент")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="user_access", to="catalog.product", verbose_name="Товар")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="digital_access", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
            ],
            options={
                "verbose_name": "Доступ пользователя к цифровому товару",
                "verbose_name_plural": "Доступы пользователей к цифровым товарам",
                "unique_together": {("user", "product", "digital_item")},
            },
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["status", "created_at"], name="orders_orde_status_0b1862_idx"),
        ),
    ]
