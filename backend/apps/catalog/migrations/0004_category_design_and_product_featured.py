from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_add_review_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="icon",
            field=models.CharField(blank=True, help_text="Например 🎮 или буква", max_length=8, verbose_name="Иконка (emoji или короткий код)"),
        ),
        migrations.AddField(
            model_name="category",
            name="color",
            field=models.CharField(blank=True, default="#4f46e5", help_text="Цвет акцента, напр. #4f46e5", max_length=9, verbose_name="Цвет (HEX)"),
        ),
        migrations.AddField(
            model_name="category",
            name="image_url",
            field=models.URLField(blank=True, help_text="Опционально: изображение-обложка категории", max_length=500, verbose_name="URL изображения"),
        ),
        migrations.AddField(
            model_name="category",
            name="featured",
            field=models.BooleanField(db_index=True, default=False, verbose_name="На главной"),
        ),
        migrations.AddField(
            model_name="product",
            name="is_featured",
            field=models.BooleanField(db_index=True, default=False, verbose_name="Рекомендуемый"),
        ),
        migrations.AddField(
            model_name="product",
            name="discount_price",
            field=models.DecimalField(blank=True, decimal_places=2, help_text="Если задана — отображается как цена, а старая зачёркивается", max_digits=10, null=True, verbose_name="Цена со скидкой"),
        ),
    ]
