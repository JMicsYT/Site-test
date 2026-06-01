from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

from django.conf import settings

from apps.orders.models import Order


@dataclass
class PaymentInitResult:
    redirect_url: str
    provider_reference: str


class PaymentProvider(ABC):
    @abstractmethod
    def init_payment(self, order: Order) -> PaymentInitResult:
        raise NotImplementedError

    @abstractmethod
    def handle_callback(self, data: Dict[str, Any]) -> Order:
        raise NotImplementedError


class StubPaymentProvider(PaymentProvider):
    """
    Заглушка платёжного провайдера.
    Эмулирует редирект и успешную оплату.
    """

    def __init__(self):
        self.callback_url = settings.PAYMENT_PROVIDER.get("CALLBACK_URL")

    def init_payment(self, order: Order) -> PaymentInitResult:
        ref = f"STUB-{order.pk}"
        redirect_url = f"https://payments.stub/checkout?order={order.pk}&ref={ref}"
        return PaymentInitResult(redirect_url=redirect_url, provider_reference=ref)

    def handle_callback(self, data: Dict[str, Any]) -> Order | None:
        """
        Ожидаем data = {"order_id": int, "status": "success"|"failed", "transaction_id": str}.
        Обрабатывает только заказы в статусе PENDING (идемпотентность).
        """
        from apps.orders.services import apply_payment_result

        try:
            order_id = int(data.get("order_id", 0))
        except (TypeError, ValueError):
            return None
        if order_id <= 0:
            return None
        order = Order.objects.filter(pk=order_id).first()
        if not order or order.status != Order.Status.PENDING:
            return None
        status = data.get("status", "failed")
        transaction_id = str(data.get("transaction_id", ""))[:128]
        apply_payment_result(order, status=status, transaction_id=transaction_id)
        return order


def get_payment_provider() -> PaymentProvider:
    # В реальном проекте можно динамически импортировать класс по строке
    return StubPaymentProvider()

