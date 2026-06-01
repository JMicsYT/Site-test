"""
Сервис создания уведомлений. Пишет в БД и, если Channels-слой доступен,
отправляет push в пользовательскую группу user_{id}.
"""
from __future__ import annotations

import logging
from typing import Optional

from .models import Notification

logger = logging.getLogger("apps")


def _push_to_channel(user_id: int, payload: dict) -> None:
    """Отправить данные в группу WS. Если channels не установлен — no-op."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
    except ImportError:
        return
    layer = get_channel_layer()
    if not layer:
        return
    try:
        async_to_sync(layer.group_send)(
            f"user_{user_id}",
            {"type": "notify", "payload": payload},
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("WS push failed: %s", exc)


def notify(
    user,
    *,
    type: str = Notification.Type.SYSTEM,
    title: str,
    body: str = "",
    url: str = "",
) -> Optional[Notification]:
    """Создать уведомление + отправить его в WS-канал пользователя."""
    if not user or not getattr(user, "pk", None):
        return None
    n = Notification.objects.create(
        user=user, type=type, title=title, body=body, url=url,
    )
    _push_to_channel(user.pk, n.to_dict())
    return n
