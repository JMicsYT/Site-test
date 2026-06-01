"""Сервис работы с кошельком — только через эти функции, чтобы не было
рассинхрона между balance у Wallet и суммой WalletTransaction."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from django.db import transaction

from .models import Wallet, WalletTransaction


class InsufficientFunds(Exception):
    """Недостаточно средств на балансе для списания."""


@transaction.atomic
def deposit(
    wallet: Wallet,
    amount: Decimal,
    *,
    tx_type: str = WalletTransaction.TxType.DEPOSIT,
    order=None,
    description: str = "",
    meta: Optional[dict] = None,
) -> WalletTransaction:
    """Пополнение кошелька. amount > 0."""
    amount = Decimal(amount).quantize(Decimal("0.01"))
    if amount <= 0:
        raise ValueError("amount должен быть положительным")
    w = Wallet.objects.select_for_update().get(pk=wallet.pk)
    w.balance = (w.balance or Decimal("0")) + amount
    w.save(update_fields=["balance", "updated_at"])
    return WalletTransaction.objects.create(
        wallet=w,
        tx_type=tx_type,
        amount=amount,
        balance_after=w.balance,
        order=order,
        description=description or "",
        meta=meta or {},
    )


@transaction.atomic
def withdraw(
    wallet: Wallet,
    amount: Decimal,
    *,
    tx_type: str = WalletTransaction.TxType.WITHDRAW,
    order=None,
    description: str = "",
    meta: Optional[dict] = None,
    allow_partial: bool = False,
) -> tuple[WalletTransaction, Decimal]:
    """
    Списание с кошелька. amount > 0.
    Возвращает (транзакция, реально списанная сумма).
    Если allow_partial=True и средств не хватает — списывает, сколько есть.
    """
    amount = Decimal(amount).quantize(Decimal("0.01"))
    if amount <= 0:
        raise ValueError("amount должен быть положительным")
    w = Wallet.objects.select_for_update().get(pk=wallet.pk)
    available = w.balance or Decimal("0")
    take = min(amount, available) if allow_partial else amount
    if take > available:
        raise InsufficientFunds(f"Недостаточно средств: {available} < {amount}")
    w.balance = available - take
    w.save(update_fields=["balance", "updated_at"])
    tx = WalletTransaction.objects.create(
        wallet=w,
        tx_type=tx_type,
        amount=(-take),
        balance_after=w.balance,
        order=order,
        description=description or "",
        meta=meta or {},
    )
    return tx, take
