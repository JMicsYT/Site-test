"""
Симметричное шифрование чувствительных полей в БД (Fernet).
Используется для DigitalItem.value — чтобы дамп БД не раскрывал цифровые ключи.
"""
from __future__ import annotations

import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


_ENC_PREFIX = "enc:v1:"


def _get_fernet() -> Optional[Fernet]:
    """Возвращает Fernet или None если ключ не задан."""
    key = getattr(settings, "FIELD_ENCRYPTION_KEY", "") or ""
    if not key:
        return None
    # Если ключ передан как произвольная строка — приводим к корректному формату
    # через SHA256 + base64 (детерминированно).
    if len(key) == 44 and key.endswith("="):
        fernet_key = key.encode()
    else:
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        fernet_key = base64.urlsafe_b64encode(digest)
    try:
        return Fernet(fernet_key)
    except Exception:
        return None


def encrypt_value(plain: str) -> str:
    """
    Шифрует строку. Если ключ не задан — возвращает plain как есть (обратная совместимость).
    Возвращает строку с префиксом 'enc:v1:' для шифрованных значений.
    """
    if plain is None:
        return ""
    if not isinstance(plain, str):
        plain = str(plain)
    if plain.startswith(_ENC_PREFIX):
        return plain  # уже зашифровано
    f = _get_fernet()
    if f is None:
        return plain
    token = f.encrypt(plain.encode("utf-8")).decode("ascii")
    return f"{_ENC_PREFIX}{token}"


def decrypt_value(stored: str) -> str:
    """
    Расшифровывает строку. Если значение без префикса — возвращает как есть.
    Если ключ неверный или данные повреждены — возвращает '' (fail-safe).
    """
    if not stored:
        return ""
    if not stored.startswith(_ENC_PREFIX):
        return stored
    f = _get_fernet()
    if f is None:
        return ""
    token = stored[len(_ENC_PREFIX):].encode("ascii")
    try:
        return f.decrypt(token).decode("utf-8")
    except (InvalidToken, ValueError):
        return ""


def is_encrypted(value: str) -> bool:
    return bool(value) and value.startswith(_ENC_PREFIX)
