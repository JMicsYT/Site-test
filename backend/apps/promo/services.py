"""Сервис применения промокодов с защитой от повторных активаций."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from django.db import transaction

from .models import Coupon, CouponUsage


class CouponError(Exception):
    """Общая ошибка применения промокода."""


def find_coupon(code: str) -> Optional[Coupon]:
    """Поиск активного промокода по коду (регистронезависимо)."""
    code = (code or "").strip()
    if not code:
        return None
    return Coupon.objects.filter(code__iexact=code).first()


def validate_for_user(coupon: Coupon, user, amount: Decimal) -> None:
    """Бросает CouponError с понятным сообщением, если промокод нельзя применить."""
    if not coupon.is_valid():
        raise CouponError("Промокод недействителен или срок его действия истёк.")
    if coupon.min_order_amount and amount < coupon.min_order_amount:
        raise CouponError(
            f"Минимальная сумма заказа для этого промокода: {coupon.min_order_amount} ₽."
        )
    if coupon.once_per_user and user and user.is_authenticated:
        if CouponUsage.objects.filter(coupon=coupon, user=user).exists():
            raise CouponError("Этот промокод уже был использован вашим аккаунтом.")


@transaction.atomic
def register_usage(
    coupon: Coupon, user, order, discount_amount: Decimal
) -> CouponUsage:
    """
    Атомарно фиксирует факт использования промокода:
      - select_for_update() — защищает от гонки при одновременной активации;
      - инкремент uses_count;
      - создание CouponUsage.
    """
    locked = Coupon.objects.select_for_update().get(pk=coupon.pk)
    if not locked.is_valid():
        raise CouponError("Промокод больше не действителен.")
    locked.uses_count = (locked.uses_count or 0) + 1
    locked.save(update_fields=["uses_count"])
    return CouponUsage.objects.create(
        coupon=locked,
        user=user if (user and user.is_authenticated) else None,
        order=order,
        discount_amount=discount_amount,
    )
