from decimal import Decimal

from django.db import transaction

from apps.catalog.models import DigitalItem, Product
from .models import Order, OrderEvent, OrderItem, UserDigitalAccess


@transaction.atomic
def create_order_for_user(user, products_with_qty, *, coupon=None, wallet_apply: Decimal | None = None):
    """
    products_with_qty: iterable[(Product, qty)] или [(product_id, qty)]
    coupon: apps.promo.models.Coupon или None — применяется к итоговой сумме.
    wallet_apply: Decimal или None — сколько списать с баланса пользователя
                  сверх скидки (до 100% от остатка к оплате).
    """
    normalized = []
    for p, qty in products_with_qty:
        try:
            qty = max(1, min(int(qty), 99))
        except (TypeError, ValueError):
            continue
        product = p
        if isinstance(p, int):
            try:
                product = Product.objects.get(pk=p, status="active")
            except Product.DoesNotExist:
                continue
        normalized.append((product, qty))

    if not normalized:
        raise ValueError("Нет допустимых товаров для заказа")

    # Цена каждой позиции — с учётом скидки товара (discount_price)
    items_total = sum(p.final_price * qty for p, qty in normalized)
    amount = Decimal(items_total)
    meta: dict = {"items_total": str(amount)}

    # Промокод
    coupon_discount = Decimal("0")
    if coupon is not None:
        from apps.promo.services import register_usage, validate_for_user
        validate_for_user(coupon, user, amount)
        coupon_discount = coupon.compute_discount(amount)
        amount = (amount - coupon_discount).quantize(Decimal("0.01"))
        meta["coupon_code"] = coupon.code
        meta["coupon_discount"] = str(coupon_discount)

    # Списание с кошелька
    wallet_used = Decimal("0")
    if wallet_apply and wallet_apply > 0 and user and user.is_authenticated:
        from apps.wallet.models import get_or_create_wallet
        from apps.wallet.services import withdraw
        w = get_or_create_wallet(user)
        to_use = min(Decimal(wallet_apply), amount, w.balance or Decimal("0"))
        if to_use > 0:
            # Списание откладываем до создания заказа, чтобы order_id был в транзакции
            wallet_used = to_use
            amount = (amount - to_use).quantize(Decimal("0.01"))
            meta["wallet_used"] = str(to_use)

    order = Order.objects.create(
        user=user, amount=amount, currency="RUB", meta=meta,
    )
    for product, qty in normalized:
        OrderItem.objects.create(
            order=order,
            product=product,
            price=product.final_price,
            quantity=qty,
        )

    # Применяем wallet списание после создания заказа (привязка к order)
    if wallet_used > 0:
        from apps.wallet.models import get_or_create_wallet
        from apps.wallet.services import withdraw
        w = get_or_create_wallet(user)
        withdraw(
            w, wallet_used,
            order=order,
            description=f"Оплата заказа #{order.pk} с баланса",
        )

    # Применяем купон после создания заказа
    if coupon is not None and coupon_discount > 0:
        from apps.promo.services import register_usage
        register_usage(coupon, user, order, coupon_discount)

    OrderEvent.objects.create(
        order=order,
        event_type=OrderEvent.EventType.CREATED,
        description=f"Заказ создан на сумму {amount} RUB",
        actor=user if (user and user.is_authenticated) else None,
        meta=meta,
    )
    return order


@transaction.atomic
def apply_payment_result(order: Order, status: str, transaction_id: str = ""):
    """
    Обновляет статус заказа и выдаёт товары. Идемпотентно:
    повторный callback для уже оплаченного заказа не дублирует выдачу.

    Используем select_for_update(): если два callback-a придут одновременно,
    второй будет ждать коммита первого и увидит уже изменённый статус.
    """
    locked = Order.objects.select_for_update().filter(pk=order.pk).first()
    if locked is None:
        return
    order = locked

    if order.status == Order.Status.PAID:
        return
    if order.status not in (Order.Status.PENDING, Order.Status.CREATED):
        return

    if status == "success":
        order.status = Order.Status.PAID
    else:
        order.status = Order.Status.FAILED

    if transaction_id:
        order.transaction_id = transaction_id
    order.save(update_fields=["status", "transaction_id", "updated_at"])

    if order.status == Order.Status.PAID:
        _fulfill_order(order)


def _fulfill_order(order: Order):
    """
    Автоматическая выдача цифровых товаров.
    """
    for item in order.items.select_related("product"):
        # Берем доступный DigitalItem
        digital_item = (
            DigitalItem.objects.select_for_update()
            .filter(product=item.product, status=DigitalItem.ItemStatus.AVAILABLE)
            .first()
        )
        if digital_item:
            digital_item.status = DigitalItem.ItemStatus.SOLD
            digital_item.save(update_fields=["status"])
        UserDigitalAccess.objects.create(
            user=order.user,
            product=item.product,
            digital_item=digital_item,
        )

