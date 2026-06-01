# Generated for Category, Product, ProductMedia, DigitalItem, Review

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
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, verbose_name="Название")),
                ("slug", models.SlugField(db_index=True, max_length=255, unique=True, verbose_name="Слаг")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("sort_order", models.PositiveIntegerField(db_index=True, default=0, verbose_name="Порядок")),
            ],
            options={
                "verbose_name": "Категория",
                "verbose_name_plural": "Категории",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=255, verbose_name="Название")),
                ("slug", models.SlugField(db_index=True, max_length=255, unique=True, verbose_name="Слаг")),
                ("short_description", models.CharField(max_length=512, verbose_name="Краткое описание")),
                ("description", models.TextField(verbose_name="Полное описание")),
                ("price", models.DecimalField(db_index=True, decimal_places=2, max_digits=10, verbose_name="Цена")),
                ("product_type", models.CharField(db_index=True, max_length=32, verbose_name="Тип товара")),
                ("license_type", models.CharField(db_index=True, max_length=32, verbose_name="Тип лицензии")),
                ("purpose", models.CharField(db_index=True, max_length=16, verbose_name="Назначение")),
                ("status", models.CharField(db_index=True, default="active", max_length=16, verbose_name="Статус")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Создан")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлён")),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="products", to="catalog.category", verbose_name="Категория")),
            ],
            options={
                "verbose_name": "Товар",
                "verbose_name_plural": "Товары",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="DigitalItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("item_type", models.CharField(max_length=32, verbose_name="Тип")),
                ("value", models.TextField(verbose_name="Значение")),
                ("max_activations", models.PositiveIntegerField(default=1, verbose_name="Количество активаций")),
                ("status", models.CharField(db_index=True, default="available", max_length=16, verbose_name="Статус")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="digital_items", to="catalog.product", verbose_name="Товар")),
            ],
            options={
                "verbose_name": "Цифровой элемент",
                "verbose_name_plural": "Цифровые элементы",
            },
        ),
        migrations.CreateModel(
            name="ProductMedia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("media_type", models.CharField(max_length=16, verbose_name="Тип")),
                ("url", models.URLField(max_length=500, verbose_name="URL")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="media", to="catalog.product", verbose_name="Товар")),
            ],
            options={
                "verbose_name": "Медиа товара",
                "verbose_name_plural": "Медиа товаров",
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rating", models.PositiveSmallIntegerField(default=5, verbose_name="Рейтинг")),
                ("text", models.TextField(blank=True, verbose_name="Отзыв")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создан")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to="catalog.product", verbose_name="Товар")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviews", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
            ],
            options={
                "verbose_name": "Отзыв",
                "verbose_name_plural": "Отзывы",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="digitalitem",
            index=models.Index(fields=["status"], name="catalog_dig_status_8a0b0d_idx"),
        ),
    ]
