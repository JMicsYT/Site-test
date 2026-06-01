"""
Добавление полей реферальной программы в пользовательскую модель.

Порядок операций специально разбит на три шага, чтобы миграция прошла
на уже заполненной БД (во всех существующих юзерах referral_code будет
пустым и нарушит UNIQUE):

    1) AddField referral_code без unique
    2) data-migration: проставляем уникальные коды всем существующим юзерам
    3) AlterField referral_code: включаем unique=True
"""
import secrets

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def _generate_unique_code(User, existing: set) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for _ in range(20):
        code = "".join(secrets.choice(alphabet) for _ in range(8))
        if code in existing:
            continue
        if User.objects.filter(referral_code=code).exists():
            continue
        existing.add(code)
        return code
    fallback = secrets.token_urlsafe(10)[:16]
    existing.add(fallback)
    return fallback


def forwards_populate_referral_code(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    existing = set(
        User.objects.exclude(referral_code="").values_list("referral_code", flat=True)
    )
    for user in User.objects.filter(referral_code=""):
        user.referral_code = _generate_unique_code(User, existing)
        user.save(update_fields=["referral_code"])


def backwards_noop(apps, schema_editor):
    # Обратное действие бессмысленно (значения уже валидные).
    return


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_user_backup_codes_user_failed_login_attempts_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="referral_bonus_paid",
            field=models.BooleanField(
                default=False,
                verbose_name="Реферальный бонус пригласившему выплачен",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="referral_code",
            field=models.CharField(
                blank=True, default="", max_length=16, verbose_name="Реферальный код",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="user",
            name="referred_by",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="referrals",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Пригласивший",
            ),
        ),
        migrations.RunPython(
            forwards_populate_referral_code,
            backwards_noop,
        ),
        migrations.AlterField(
            model_name="user",
            name="referral_code",
            field=models.CharField(
                blank=True, db_index=True, max_length=16, unique=True,
                verbose_name="Реферальный код",
            ),
        ),
    ]
