"""
Отправка алертов администратору в Telegram через Bot API.

Использование:
    from apps.core.telegram import notify_admin
    notify_admin(f"Новый заказ #{order.pk} на {order.amount} ₽")

Если TELEGRAM_NOTIFICATIONS_ENABLED=False (либо не заданы токены),
функция безопасно ничего не делает.
"""
from __future__ import annotations

import json
import logging
from typing import Optional
from urllib import parse, request as urlreq

from django.conf import settings

_log = logging.getLogger("apps")


def _enabled() -> bool:
    return bool(
        getattr(settings, "TELEGRAM_NOTIFICATIONS_ENABLED", False)
        and getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        and getattr(settings, "TELEGRAM_ADMIN_CHAT_ID", "")
    )


def notify_admin(text: str, *, parse_mode: str = "HTML", silent: bool = False) -> bool:
    """Отправляет сообщение в Telegram. Возвращает True при успехе."""
    if not _enabled():
        return False
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text[:4000],
        "parse_mode": parse_mode,
        "disable_notification": silent,
        "disable_web_page_preview": True,
    }
    try:
        data = parse.urlencode(payload).encode("utf-8")
        req = urlreq.Request(url, data=data, method="POST")
        with urlreq.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            ok = '"ok":true' in body
            if not ok:
                _log.warning("Telegram API ответил не ok: %s", body[:200])
            return ok
    except Exception as exc:  # noqa: BLE001
        _log.warning("Не удалось отправить Telegram-уведомление: %s", exc)
        return False


def notify_admin_async(text: str, **kwargs) -> None:
    """Fire-and-forget отправка в отдельном потоке.

    Используем, когда вызов из обработчика HTTP-запроса — чтобы не блокировать ответ.
    """
    if not _enabled():
        return
    import threading
    t = threading.Thread(
        target=notify_admin, args=(text,), kwargs=kwargs, daemon=True
    )
    t.start()
