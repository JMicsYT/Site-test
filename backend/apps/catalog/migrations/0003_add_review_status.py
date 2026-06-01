# Generated manually for Review.status

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_rename_catalog_dig_status_8a0b0d_idx_catalog_dig_status_f54eaa_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="review",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "На модерации"),
                    ("published", "Опубликован"),
                    ("hidden", "Скрыт"),
                ],
                db_index=True,
                default="pending",
                max_length=16,
                verbose_name="Статус",
            ),
        ),
    ]
