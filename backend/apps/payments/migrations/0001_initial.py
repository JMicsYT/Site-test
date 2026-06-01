# Generated for PaymentNotification

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PaymentNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("raw_data", models.JSONField(verbose_name="Сырые данные")),
                ("processed", models.BooleanField(default=False, verbose_name="Обработано")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payment_notifications", to="orders.order", verbose_name="Заказ")),
            ],
            options={
                "verbose_name": "Платёжное уведомление",
                "verbose_name_plural": "Платёжные уведомления",
                "ordering": ["-created_at"],
            },
        ),
    ]
