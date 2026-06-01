"""
Одноразовые подписанные ссылки на получение цифрового товара.

Принцип:
- После оплаты клиент получает кнопку/ссылку с signed-токеном TimestampSigner.
- Токен привязан к (access_id, user_id, jti). Кликнув по ссылке, пользователь
  попадает на RevealDigitalItemView — view проверяет токен, TTL, лимит использований
  и возвращает plain-значение (ключ/ссылка/код).
- Каждый переход пишется в DownloadAudit. Счётчик использований хранится в кеше
  по ключу jti, чтобы токен нельзя было реиспользовать бесконечно.
"""
from __future__ import annotations

import secrets
from typing import Optional

from django.conf import settings
from django.core.cache import cache
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.http import HttpRequest


_SIGNER_SALT = "shoshop.digital-access.v1"


def _signer() -> TimestampSigner:
    return TimestampSigner(
        key=getattr(settings, "DOWNLOAD_LINK_SECRET", settings.SECRET_KEY),
        salt=_SIGNER_SALT,
    )


def generate_signed_token(access_id: int, user_id: int) -> str:
    """
    Генерирует токен: 'access_id:user_id:jti', подписанный TimestampSigner.
    jti — уникальный идентификатор конкретного токена (нужен для счётчика использований).
    """
    jti = secrets.token_urlsafe(12)
    payload = f"{access_id}:{user_id}:{jti}"
    return _signer().sign(payload)


def parse_signed_token(token: str) -> Optional[dict]:
    """
    Проверяет подпись и TTL. Возвращает dict(access_id, user_id, jti) или None.
    """
    if not token:
        return None
    ttl = int(getattr(settings, "DOWNLOAD_LINK_TTL", 900))
    try:
        payload = _signer().unsign(token, max_age=ttl)
    except (BadSignature, SignatureExpired):
        return None
    try:
        access_id_s, user_id_s, jti = payload.split(":", 2)
        return {
            "access_id": int(access_id_s),
            "user_id": int(user_id_s),
            "jti": jti,
        }
    except (ValueError, AttributeError):
        return None


def register_use(jti: str) -> tuple[bool, int]:
    """
    Увеличивает счётчик использований токена.
    Возвращает (allowed, current_count). Если превышен лимит — allowed=False.
    """
    max_uses = int(getattr(settings, "DOWNLOAD_LINK_MAX_USES", 3))
    key = f"dl-token-uses:{jti}"
    count = cache.get(key, 0)
    if count >= max_uses:
        return False, count
    ttl = int(getattr(settings, "DOWNLOAD_LINK_TTL", 900)) + 60
    try:
        new_val = cache.incr(key)
    except ValueError:
        cache.set(key, 1, ttl)
        new_val = 1
    if new_val == 1:
        cache.expire(key, ttl) if hasattr(cache, "expire") else cache.set(key, new_val, ttl)
    return True, new_val


def get_client_ip(request: HttpRequest) -> Optional[str]:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
