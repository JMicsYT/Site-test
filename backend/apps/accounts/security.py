"""
Утилиты безопасности: 2FA (TOTP), коды восстановления, HIBP-проверка пароля.
"""
from __future__ import annotations

import base64
import hashlib
import io
import secrets
from typing import List, Tuple
from urllib import request as urllib_request
from urllib.error import URLError

import pyotp
import qrcode
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password


TOTP_ISSUER = "ShoShop"


def generate_totp_secret() -> str:
    """Криптостойкий 160-битный секрет для TOTP, base32."""
    return pyotp.random_base32()


def build_totp_uri(user_email: str, secret: str) -> str:
    """otpauth:// URI для QR-кода."""
    return pyotp.TOTP(secret).provisioning_uri(name=user_email, issuer_name=TOTP_ISSUER)


def qr_png_data_uri(otpauth_uri: str) -> str:
    """Генерирует data:image/png;base64 для отрисовки QR без внешних запросов."""
    img = qrcode.make(otpauth_uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def verify_totp(secret: str, code: str) -> bool:
    """Проверяет TOTP-код с окном ±1 (±30 сек) — компенсирует расхождение часов."""
    if not secret or not code:
        return False
    code = code.strip().replace(" ", "")
    if not code.isdigit() or len(code) != 6:
        return False
    try:
        return pyotp.TOTP(secret).verify(code, valid_window=1)
    except Exception:
        return False


# ===== Backup-коды =====

BACKUP_CODE_COUNT = 10
BACKUP_CODE_LEN = 10


def generate_backup_codes() -> Tuple[List[str], List[str]]:
    """
    Возвращает (plain_codes, hashed_codes). Показываем plain пользователю один раз,
    в БД храним только hash (pbkdf2 через Django hasher).
    """
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # без похожих символов
    plain_codes: List[str] = []
    for _ in range(BACKUP_CODE_COUNT):
        code = "".join(secrets.choice(alphabet) for _ in range(BACKUP_CODE_LEN))
        plain_codes.append(f"{code[:5]}-{code[5:]}")
    hashed = [make_password(c) for c in plain_codes]
    return plain_codes, hashed


def consume_backup_code(hashed_codes: List[str], provided: str) -> Tuple[bool, List[str]]:
    """
    Проверяет provided-код. Если совпал с каким-то хэшем — удаляет его из списка.
    Возвращает (matched, new_hashed_list).
    """
    if not provided:
        return False, hashed_codes
    provided = provided.strip().upper()
    for i, h in enumerate(hashed_codes):
        if check_password(provided, h):
            new_list = list(hashed_codes)
            new_list.pop(i)
            return True, new_list
    return False, hashed_codes


# ===== HIBP =====

HIBP_URL = "https://api.pwnedpasswords.com/range/{prefix}"


def hibp_check_password(password: str, timeout: float = 2.5) -> int:
    """
    Проверка пароля через HIBP (k-anonymity): отправляем только первые 5 символов
    SHA1-хэша пароля, HIBP возвращает список суффиксов со счётчиком утечек.

    Возвращает количество найденных утечек (0 — пароль чист, >0 — скомпрометирован).
    При ошибке сети — 0 (fail-open, чтобы не блокировать регистрацию).
    """
    if not password or len(password) < 4:
        return 0
    if not getattr(settings, "HIBP_CHECK_ENABLED", True):
        return 0

    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    url = HIBP_URL.format(prefix=prefix)
    try:
        req = urllib_request.Request(url, headers={"User-Agent": "ShoShop-Security/1.0"})
        with urllib_request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return 0
            body = resp.read().decode("utf-8", errors="replace")
    except (URLError, TimeoutError, OSError):
        return 0

    for line in body.splitlines():
        if not line:
            continue
        try:
            part_suffix, part_count = line.split(":", 1)
        except ValueError:
            continue
        if part_suffix.strip().upper() == suffix:
            try:
                return int(part_count.strip())
            except ValueError:
                return 1
    return 0
