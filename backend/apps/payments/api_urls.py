import hashlib
import hmac
import json
import time

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.crypto import constant_time_compare
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import path

from apps.core.audit import log_event

from .models import PaymentNotification
from .providers import get_payment_provider


def _parse_callback_body(request):
    """Парсит тело запроса: JSON или form-urlencoded."""
    content_type = request.content_type or ""
    if "application/json" in content_type and request.body:
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            return None
    return request.POST.dict()


def _verify_callback_secret(request, data):
    """
    Проверка подлинности callback. Поддерживает два режима:

    1. HMAC (рекомендуется): заголовок X-Signature содержит hex HMAC-SHA256
       по сырому телу запроса с использованием CALLBACK_SECRET.
       Для защиты от replay-атак — заголовок X-Timestamp (unix-секунды)
       обязателен, и он включается в вычисление HMAC как '{ts}.{body}'.
       Окно валидности — PAYMENT_CALLBACK_REPLAY_WINDOW (по умолчанию 300 с).
       Nonce (из тела payload.nonce или X-Nonce) кешируется на время окна,
       чтобы каждый callback можно было принять только один раз.

    2. Совместимый (legacy): заголовок X-Payment-Secret или поле callback_secret
       в теле. Оставлен для обратной совместимости и для stub-провайдера.
    """
    payment_config = getattr(settings, "PAYMENT_PROVIDER", {})
    secret = payment_config.get("CALLBACK_SECRET", "")
    if not secret:
        return True

    # Режим 1: HMAC с timestamp + nonce
    sig_header = request.headers.get("X-Signature") or ""
    ts_header = request.headers.get("X-Timestamp") or ""
    if sig_header and ts_header:
        try:
            ts_int = int(ts_header)
        except ValueError:
            return False
        window = int(getattr(settings, "PAYMENT_CALLBACK_REPLAY_WINDOW", 300))
        now = int(time.time())
        if abs(now - ts_int) > window:
            return False
        raw_body = request.body or b""
        message = f"{ts_header}.".encode("utf-8") + raw_body
        expected = hmac.new(
            secret.encode("utf-8"), message, hashlib.sha256
        ).hexdigest()
        if not constant_time_compare(expected, sig_header.strip()):
            return False

        nonce = request.headers.get("X-Nonce") or (
            data.get("nonce") if isinstance(data, dict) else None
        )
        if nonce:
            key = f"pay-nonce:{nonce}"
            if cache.get(key):
                return False
            cache.set(key, 1, window + 60)
        return True

    # Режим 2: legacy
    provided = (
        request.headers.get("X-Payment-Secret")
        or (data.get("callback_secret") if isinstance(data, dict) else None)
        or (data.get("secret") if isinstance(data, dict) else None)
        or ""
    )
    return constant_time_compare(provided, secret)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(require_POST, name="dispatch")
class PaymentCallbackView(View):
    def post(self, request):
        data = _parse_callback_body(request)
        if data is None:
            return JsonResponse({"status": "error", "message": "Invalid body"}, status=400)
        if not isinstance(data, dict):
            data = {}
        if not _verify_callback_secret(request, data):
            log_event(
                "payment_callback_fail",
                request=request,
                description="Неверная подпись/timestamp/nonce callback",
                meta={"order_id": data.get("order_id")},
            )
            return JsonResponse({"status": "forbidden"}, status=403)
        provider = get_payment_provider()
        order = provider.handle_callback(data)
        if order:
            PaymentNotification.objects.create(order=order, raw_data=data, processed=True)
            log_event(
                "payment_callback_ok",
                request=request,
                description=f"Callback обработан для заказа #{order.pk}",
                meta={"order_id": order.pk, "status": order.status},
            )
            if order.status == "paid":
                log_event(
                    "order_paid",
                    request=request,
                    user=order.user,
                    description=f"Заказ #{order.pk} оплачен",
                    meta={"order_id": order.pk, "amount": str(order.amount)},
                )
        return JsonResponse({"status": "ok"})


urlpatterns = [
    path("callback/", PaymentCallbackView.as_view(), name="callback"),
]

