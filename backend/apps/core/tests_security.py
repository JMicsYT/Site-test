"""
Тесты безопасности (15+ сценариев) — соответствие OWASP Top-10 и требованиям ФЗ-152.

Запуск:
    python manage.py test apps.core.tests_security -v 2
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.security import (
    consume_backup_code,
    generate_backup_codes,
    generate_totp_secret,
    verify_totp,
)
from apps.catalog.models import Category, DigitalItem, Product
from apps.core.audit import log_event
from apps.core.crypto import decrypt_value, encrypt_value, is_encrypted
from apps.core.models import DownloadAudit, SecurityEvent
from apps.orders.downloads import (
    generate_signed_token,
    parse_signed_token,
    register_use,
)
from apps.orders.models import Order, UserDigitalAccess


# ==== ALLOWED_HOSTS для тестового клиента ====
if "testserver" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append("testserver")


# ==== Monkey-patch для Python 3.14 + Django 5.0 ====
# В Django 5.0 Context.__copy__ вызывает super().__copy__() которого нет в
# новом Python. Это ломает instrumented_test_render (store_rendered_templates).
# Ставим простую реализацию.
try:
    from django.template.context import BaseContext, Context
    def _safe_copy(self):
        import copy as _copy
        dup = _copy.copy.__wrapped__(self) if hasattr(_copy.copy, "__wrapped__") else self.__class__.__new__(self.__class__)
        dup.__dict__.update(self.__dict__)
        dup.dicts = self.dicts[:]
        return dup
    BaseContext.__copy__ = _safe_copy
except Exception:
    pass


def _make_user(email="user@test.local", password="StrongPa$$w0rd-xyz", **kw):
    return User.objects.create_user(email=email, password=password, **kw)


def _make_product(price="10.00"):
    cat = Category.objects.create(name="Test", slug="test")
    return Product.objects.create(
        category=cat,
        name="Test Product",
        slug="test-product",
        short_description="sd",
        description="d",
        price=Decimal(price),
        product_type="software",
        license_type="perpetual",
        purpose="personal",
        status="active",
    )


class TwoFactorTests(TestCase):
    """A07: 2FA TOTP + backup-коды."""

    def test_totp_secret_is_unique_and_valid(self):
        s1 = generate_totp_secret()
        s2 = generate_totp_secret()
        self.assertNotEqual(s1, s2)
        self.assertEqual(len(s1), 32)

    def test_totp_verify_accepts_valid_code(self):
        import pyotp
        secret = generate_totp_secret()
        code = pyotp.TOTP(secret).now()
        self.assertTrue(verify_totp(secret, code))

    def test_totp_verify_rejects_invalid_code(self):
        secret = generate_totp_secret()
        self.assertFalse(verify_totp(secret, "000000"))
        self.assertFalse(verify_totp(secret, "abc"))
        self.assertFalse(verify_totp(secret, ""))

    def test_backup_codes_generation_and_consume(self):
        plain, hashed = generate_backup_codes()
        self.assertEqual(len(plain), 10)
        self.assertEqual(len(hashed), 10)
        # Ни один hash не равен самому коду (храним только хэш)
        for p, h in zip(plain, hashed):
            self.assertNotEqual(p, h)
        ok, new_hashed = consume_backup_code(hashed, plain[0])
        self.assertTrue(ok)
        self.assertEqual(len(new_hashed), 9)
        # Повторное использование того же кода — не сработает
        ok2, _ = consume_backup_code(new_hashed, plain[0])
        self.assertFalse(ok2)


class AccountLockoutTests(TestCase):
    """A04: блокировка после N неудач."""

    def setUp(self):
        self.user = _make_user()
        cache.clear()

    @override_settings(ACCOUNT_LOCKOUT_MAX_FAILURES=3, ACCOUNT_LOCKOUT_DURATION=1800)
    def test_account_locks_after_n_failures(self):
        c = Client()
        for _ in range(3):
            c.post(reverse("accounts:login"), {
                "email": self.user.email, "password": "wrong",
            })
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked())
        self.assertGreaterEqual(self.user.failed_login_attempts, 3)

    def test_unlock_by_token_clears_lock(self):
        self.user.failed_login_attempts = 99
        self.user.locked_until = timezone.now() + timedelta(hours=1)
        self.user.generate_unlock_token()
        self.user.save()

        c = Client()
        c.get(reverse("accounts:unlock", kwargs={"token": self.user.unlock_token}))
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_locked())
        self.assertEqual(self.user.failed_login_attempts, 0)


class UserEnumerationTests(TestCase):
    """A07: защита от user enumeration — одинаковые сообщения об ошибках."""

    def setUp(self):
        self.user = _make_user(email="exists@test.local")

    def test_login_error_is_same_for_existing_and_nonexistent(self):
        c = Client()
        r1 = c.post(reverse("accounts:login"), {
            "email": "exists@test.local", "password": "wrong",
        })
        r2 = c.post(reverse("accounts:login"), {
            "email": "nonexistent@test.local", "password": "wrong",
        })
        # Оба запроса — 200 (форма с ошибкой), сообщения одинаковые
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        # Содержимое страниц должно содержать одно и то же generic-сообщение
        self.assertIn("Неверный email", r1.content.decode())
        self.assertIn("Неверный email", r2.content.decode())


class SignedDownloadLinkTests(TestCase):
    """A08: подписанные одноразовые ссылки."""

    def test_token_roundtrip(self):
        token = generate_signed_token(access_id=42, user_id=7)
        parsed = parse_signed_token(token)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["access_id"], 42)
        self.assertEqual(parsed["user_id"], 7)
        self.assertTrue(parsed["jti"])

    def test_tampered_token_rejected(self):
        token = generate_signed_token(42, 7)
        bad = token[:-2] + ("00" if token[-1] != "0" else "11")
        self.assertIsNone(parse_signed_token(bad))

    def test_garbage_token_rejected(self):
        self.assertIsNone(parse_signed_token(""))
        self.assertIsNone(parse_signed_token("garbage"))

    def test_register_use_limits(self):
        cache.clear()
        jti = "test-jti-xyz"
        with override_settings(DOWNLOAD_LINK_MAX_USES=2):
            ok, n = register_use(jti); self.assertTrue(ok)
            ok, n = register_use(jti); self.assertTrue(ok)
            ok, n = register_use(jti); self.assertFalse(ok)


class FieldEncryptionTests(TestCase):
    """A02: шифрование чувствительных полей."""

    @override_settings(FIELD_ENCRYPTION_KEY="test-encryption-key-with-enough-entropy-xyz")
    def test_encrypt_decrypt_roundtrip(self):
        plain = "SECRET-LICENSE-KEY-12345-ABCDE"
        enc = encrypt_value(plain)
        self.assertTrue(is_encrypted(enc))
        self.assertNotIn(plain, enc)
        self.assertEqual(decrypt_value(enc), plain)

    @override_settings(FIELD_ENCRYPTION_KEY="test-encryption-key-with-enough-entropy-xyz")
    def test_encryption_is_nondeterministic(self):
        plain = "SECRET-LICENSE-KEY"
        e1 = encrypt_value(plain)
        e2 = encrypt_value(plain)
        self.assertNotEqual(e1, e2)
        self.assertEqual(decrypt_value(e1), decrypt_value(e2))

    @override_settings(FIELD_ENCRYPTION_KEY="test-encryption-key-with-enough-entropy-xyz")
    def test_digital_item_stores_ciphertext(self):
        product = _make_product()
        item = DigitalItem.objects.create(
            product=product, item_type="key", value="SUPER-SECRET-KEY-999",
        )
        item.refresh_from_db()
        self.assertTrue(is_encrypted(item.value))
        self.assertNotIn("SUPER-SECRET-KEY-999", item.value)
        self.assertEqual(item.plain_value, "SUPER-SECRET-KEY-999")


class HMACCallbackTests(TestCase):
    """A08: HMAC-подпись callback платёжной системы."""

    def setUp(self):
        cache.clear()

    def _build_signed_callback(self, body: dict, secret: str, ts: int | None = None):
        ts = ts or int(time.time())
        raw = json.dumps(body).encode()
        message = f"{ts}.".encode() + raw
        sig = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
        return raw, {
            "HTTP_X_SIGNATURE": sig,
            "HTTP_X_TIMESTAMP": str(ts),
            "HTTP_X_NONCE": f"nonce-{ts}",
        }

    @override_settings(PAYMENT_PROVIDER={"CALLBACK_SECRET": "test-secret-123"})
    def test_valid_hmac_is_accepted(self):
        c = Client()
        body = {"order_id": 999, "status": "success"}
        raw, headers = self._build_signed_callback(body, "test-secret-123")
        resp = c.post(
            "/api/payments/callback/",
            data=raw,
            content_type="application/json",
            **headers,
        )
        # Даже без заказа — подпись считается валидной (order=None, но 200)
        self.assertIn(resp.status_code, (200, 400))
        self.assertNotEqual(resp.status_code, 403)

    @override_settings(PAYMENT_PROVIDER={"CALLBACK_SECRET": "test-secret-123"})
    def test_invalid_signature_is_rejected(self):
        c = Client()
        body = {"order_id": 999, "status": "success"}
        raw = json.dumps(body).encode()
        headers = {
            "HTTP_X_SIGNATURE": "deadbeef" * 8,
            "HTTP_X_TIMESTAMP": str(int(time.time())),
        }
        resp = c.post(
            "/api/payments/callback/",
            data=raw,
            content_type="application/json",
            **headers,
        )
        self.assertEqual(resp.status_code, 403)

    @override_settings(
        PAYMENT_PROVIDER={"CALLBACK_SECRET": "test-secret-123"},
        PAYMENT_CALLBACK_REPLAY_WINDOW=60,
    )
    def test_replay_attack_is_rejected(self):
        c = Client()
        old_ts = int(time.time()) - 3600
        body = {"order_id": 999, "status": "success"}
        raw, headers = self._build_signed_callback(body, "test-secret-123", ts=old_ts)
        resp = c.post(
            "/api/payments/callback/",
            data=raw,
            content_type="application/json",
            **headers,
        )
        self.assertEqual(resp.status_code, 403)

    @override_settings(PAYMENT_PROVIDER={"CALLBACK_SECRET": "test-secret-123"})
    def test_same_nonce_is_rejected_twice(self):
        c = Client()
        body = {"order_id": 999, "status": "success"}
        raw, headers = self._build_signed_callback(body, "test-secret-123")
        # Первый запрос
        c.post("/api/payments/callback/", data=raw,
               content_type="application/json", **headers)
        # Повторный с тем же nonce
        resp2 = c.post("/api/payments/callback/", data=raw,
                       content_type="application/json", **headers)
        self.assertEqual(resp2.status_code, 403)


class AuditLogTests(TestCase):
    """A09: логирование событий безопасности."""

    def test_log_event_creates_record(self):
        user = _make_user()
        from django.test import RequestFactory
        rf = RequestFactory()
        req = rf.post("/test/", HTTP_USER_AGENT="TestBot/1.0")
        req.user = user
        log_event(
            "password_change", request=req, user=user, description="unit-test"
        )
        ev = SecurityEvent.objects.filter(event_type="password_change").first()
        self.assertIsNotNone(ev)
        self.assertEqual(ev.user_id, user.pk)
        self.assertEqual(ev.user_agent, "TestBot/1.0")

    def test_login_success_is_logged(self):
        user = _make_user()
        c = Client()
        c.post(reverse("accounts:login"), {
            "email": user.email, "password": "StrongPa$$w0rd-xyz",
        })
        self.assertTrue(
            SecurityEvent.objects.filter(
                user=user, event_type="login_success"
            ).exists()
        )


class AccessControlTests(TestCase):
    """A01: Broken Access Control."""

    def test_dashboard_requires_login(self):
        c = Client()
        resp = c.get(reverse("accounts:dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.url)

    def test_user_cannot_cancel_others_order(self):
        alice = _make_user(email="a@test.local")
        bob = _make_user(email="b@test.local")
        product = _make_product()
        order = Order.objects.create(
            user=alice,
            amount=Decimal("10.00"),
            currency="RUB",
            status=Order.Status.CREATED,
        )
        c = Client()
        c.login(email=bob.email, password="StrongPa$$w0rd-xyz")
        resp = c.post(reverse("orders:cancel", kwargs={"order_id": order.pk}))
        self.assertEqual(resp.status_code, 404)
        order.refresh_from_db()
        self.assertNotEqual(order.status, Order.Status.CANCELLED)

    def test_user_cannot_reveal_others_digital_item(self):
        alice = _make_user(email="alice@test.local")
        bob = _make_user(email="bob@test.local")
        product = _make_product()
        di = DigitalItem.objects.create(
            product=product, item_type="key", value="ALICE-ONLY-KEY",
        )
        access = UserDigitalAccess.objects.create(
            user=alice, product=product, digital_item=di,
        )
        # Токен Алисы
        token = generate_signed_token(access.pk, alice.pk)

        c = Client()
        c.login(email=bob.email, password="StrongPa$$w0rd-xyz")
        resp = c.get(reverse("orders:digital_reveal") + f"?t={token}")
        self.assertEqual(resp.status_code, 404)

        # Зафиксирован suspicious_activity
        self.assertTrue(
            SecurityEvent.objects.filter(
                event_type="suspicious_activity"
            ).exists()
        )


class SecurityHeadersTests(TestCase):
    """A05: security headers + CSP."""

    def test_response_includes_security_headers(self):
        c = Client()
        # health — простой JSON endpoint, не рендерит шаблон
        resp = c.get("/health/")
        self.assertEqual(resp["X-Content-Type-Options"], "nosniff")
        self.assertIn("strict-origin", resp["Referrer-Policy"])
        self.assertIn("frame-ancestors 'none'", resp["Content-Security-Policy"])
        self.assertEqual(resp["X-Frame-Options"], "DENY")
