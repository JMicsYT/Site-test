"""
Единая точка входа для записи событий безопасности.
Пишет одновременно в БД (SecurityEvent) и в JSON-лог (logger 'security').
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from django.http import HttpRequest

from .models import SecurityEvent

_logger = logging.getLogger("security")


def get_client_ip(request: Optional[HttpRequest]) -> Optional[str]:
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def get_user_agent(request: Optional[HttpRequest]) -> str:
    if request is None:
        return ""
    return (request.META.get("HTTP_USER_AGENT") or "")[:512]


def log_event(
    event_type: str,
    *,
    request: Optional[HttpRequest] = None,
    user: Any = None,
    description: str = "",
    meta: Optional[dict] = None,
) -> SecurityEvent:
    """
    Логирует событие безопасности.
    - Пишет в БД (SecurityEvent)
    - Пишет в файл security.log (JSON)
    """
    ip = get_client_ip(request)
    ua = get_user_agent(request)

    actual_user = None
    if user is not None and getattr(user, "pk", None):
        actual_user = user
    elif request is not None:
        ru = getattr(request, "user", None)
        if ru is not None and getattr(ru, "is_authenticated", False):
            actual_user = ru

    event = SecurityEvent.objects.create(
        user=actual_user,
        event_type=event_type,
        description=description[:2000],
        ip_address=ip,
        user_agent=ua,
        meta=meta or {},
    )

    _logger.info(
        description or event_type,
        extra={
            "event": event_type,
            "user_id": actual_user.pk if actual_user else None,
            "ip": ip,
            "path": request.path if request else None,
        },
    )
    return event
