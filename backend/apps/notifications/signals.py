"""
Сигналы, порождающие уведомления на ключевые события домена:
- заказ перешёл в статус PAID/FAILED;
- админ ответил в тикете поддержки;
- отзыв одобрен.

Дополнительно: при первой оплаченной заказе реферала пригласившему
начисляется фиксированный бонус на баланс (единожды).
"""
from __future__ import annotations

import logging
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification
from .services import notify

_log = logging.getLogger("apps")


def _pay_referral_bonus(order) -> None:
    """Пополняет кошелёк пригласившего, если это первая оплаченная покупка реферала."""
    user = getattr(order, "user", None)
    if not user or not getattr(user, "referred_by_id", None):
        return
    if getattr(user, "referral_bonus_paid", False):
        return
    bonus = Decimal(getattr(settings, "REFERRAL_BONUS_AMOUNT", 0) or 0)
    if bonus <= 0:
        return
    try:
        from apps.wallet.models import WalletTransaction, get_or_create_wallet
        from apps.wallet.services import deposit
        inviter = user.referred_by
        with transaction.atomic():
            w = get_or_create_wallet(inviter)
            deposit(
                w, bonus,
                tx_type=WalletTransaction.TxType.REFERRAL,
                description=f"Бонус за приглашение {user.email}",
                meta={"referral_user_id": user.pk, "order_id": order.pk},
            )
            user.referral_bonus_paid = True
            user.save(update_fields=["referral_bonus_paid"])
        notify(
            inviter,
            type=Notification.Type.REFERRAL_BONUS,
            title=f"Вам начислен реферальный бонус {bonus} ₽",
            body=f"Ваш приглашённый {user.email} совершил первую оплату.",
            url="/wallet/",
        )
    except Exception as exc:  # pragma: no cover
        _log.warning("Ошибка начисления реферального бонуса: %s", exc)


@receiver(post_save, sender="orders.Order")
def _on_order_saved(sender, instance, created, update_fields=None, **kwargs):
    try:
        from apps.orders.models import Order
    except Exception:
        return
    if created:
        return
    if update_fields and "status" not in update_fields:
        return
    status = instance.status
    if status == Order.Status.PAID:
        notify(
            instance.user,
            type=Notification.Type.ORDER_PAID,
            title=f"Заказ #{instance.pk} оплачен",
            body=f"Спасибо! Сумма: {instance.amount} {instance.currency}. Цифровые товары доступны в кабинете.",
            url="/accounts/dashboard/",
        )
        _pay_referral_bonus(instance)
        try:
            from apps.core.telegram import notify_admin_async
            email = getattr(instance.user, "email", "гость")
            notify_admin_async(
                f"💸 <b>Оплачен заказ #{instance.pk}</b>\n"
                f"Покупатель: {email}\n"
                f"Сумма: <b>{instance.amount} {instance.currency}</b>"
            )
        except Exception:
            pass
    elif status == Order.Status.FAILED:
        notify(
            instance.user,
            type=Notification.Type.ORDER_FAILED,
            title=f"Оплата заказа #{instance.pk} не прошла",
            body="Попробуйте оплатить заказ ещё раз или свяжитесь с поддержкой.",
            url="/accounts/orders/",
        )


@receiver(post_save, sender="core.SupportMessage")
def _on_support_message(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        ticket = instance.ticket
    except Exception:
        return
    if not ticket or not ticket.user_id:
        return
    if instance.author_id == ticket.user_id:
        # Сообщение от клиента — алерт админу
        try:
            from apps.core.telegram import notify_admin_async
            notify_admin_async(
                f"💬 <b>Новое сообщение в тикете #{ticket.pk}</b>\n"
                f"От: {getattr(ticket.user, 'email', '—')}\n"
                f"«{(instance.body or '')[:300]}»"
            )
        except Exception:
            pass
        return
    # Сообщение от админа — уведомляем клиента
    notify(
        ticket.user,
        type=Notification.Type.SUPPORT_REPLY,
        title=f"Ответ в обращении #{ticket.pk}",
        body=(instance.body or "")[:200],
        url=f"/support/ticket/{ticket.pk}/",
    )


@receiver(post_save, sender="catalog.Review")
def _on_review_saved(sender, instance, created, update_fields=None, **kwargs):
    if created:
        return
    try:
        from apps.catalog.models import Review
    except Exception:
        return
    if instance.status != Review.Status.PUBLISHED:
        return
    if not instance.user_id:
        return
    notify(
        instance.user,
        type=Notification.Type.REVIEW_APPROVED,
        title="Ваш отзыв опубликован",
        body=f"Отзыв к «{instance.product.name}» прошёл модерацию.",
        url=f"/catalog/{instance.product.slug}/",
    )
