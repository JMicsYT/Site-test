# Generated for custom User model (must run before auth/admin)

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("contenttypes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False)),
                ("email", models.EmailField(db_index=True, max_length=254, unique=True, verbose_name="Email")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="Имя")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="Фамилия")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Дата регистрации")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
                ("is_staff", models.BooleanField(default=False, verbose_name="Персонал")),
                ("email_verified", models.BooleanField(default=False, verbose_name="Email подтверждён")),
                ("role", models.CharField(choices=[("user", "Пользователь"), ("admin", "Администратор")], db_index=True, default="user", max_length=16, verbose_name="Роль")),
            ],
            options={
                "verbose_name": "Пользователь",
                "verbose_name_plural": "Пользователи",
                "ordering": ["-date_joined"],
            },
        ),
    ]
