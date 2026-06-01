from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from .views import VerifyEmailView

User = get_user_model()


class RegistrationTests(TestCase):
    def test_register_get(self):
        from .views import RegisterView

        request = RequestFactory().get(reverse("accounts:register"))
        request.session = {}
        resp = RegisterView.as_view()(request)
        self.assertEqual(resp.status_code, 200)

    def _build_register_data(self, **overrides):
        """Формирует валидный payload регистрации (включая мат-капчу)."""
        from .forms import _make_math_captcha
        cap = _make_math_captcha()
        # parse question "Сколько будет X + Y?" / "X - Y?" и посчитаем
        import re
        m = re.search(r"(\d+)\s*([+\-])\s*(\d+)", cap["question"])
        a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
        answer = str(a + b if op == "+" else a - b)
        data = {
            "email": "new@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
            "captcha_token": cap["token"],
            "captcha_answer": answer,
        }
        data.update(overrides)
        return data

    def test_register_success(self):
        from .tasks import send_email_verification_sync

        data = self._build_register_data()
        with patch("apps.accounts.views.send_email_verification") as mock_send, \
             patch("apps.accounts.forms.hibp_check_password", return_value=0):
            mock_send.delay = lambda user_id: send_email_verification_sync(user_id)
            resp = self.client.post(reverse("accounts:register"), data, follow=False)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(email="new@example.com").exists())
        user = User.objects.get(email="new@example.com")
        self.assertFalse(user.email_verified)
        self.assertIn(reverse("accounts:dashboard"), resp.url)

    def test_register_password_mismatch(self):
        data = self._build_register_data(password_confirm="OtherPass456!")
        with patch("apps.accounts.forms.hibp_check_password", return_value=0):
            resp = self.client.post(reverse("accounts:register"), data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(email="new@example.com").exists())


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="login@test.com", password="testpass123")

    def test_login_success(self):
        resp = self.client.post(
            reverse("accounts:login"),
            {"email": "login@test.com", "password": "testpass123"},
            follow=False,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:dashboard"), resp.url)

    def test_login_next_redirect(self):
        resp = self.client.post(
            reverse("accounts:login") + "?next=/catalog/",
            {"email": "login@test.com", "password": "testpass123"},
            follow=False,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/catalog/", resp.url)

    def test_login_wrong_password(self):
        from .views import LoginView

        request = RequestFactory().post(
            reverse("accounts:login"),
            {"email": "login@test.com", "password": "wrong"},
        )
        request.session = {}
        resp = LoginView.as_view()(request)
        self.assertEqual(resp.status_code, 200)


class LogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="out@test.com", password="testpass123")

    def test_logout(self):
        self.client.login(email="out@test.com", password="testpass123")
        resp = self.client.get(reverse("accounts:logout"), follow=False)
        self.assertEqual(resp.status_code, 302)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="reset@test.com", password="testpass123")

    def test_password_reset_request(self):
        resp = self.client.post(
            reverse("accounts:password_reset"),
            {"email": "reset@test.com"},
            follow=False,
        )
        self.assertIn(resp.status_code, (200, 302))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset@test.com", mail.outbox[0].to)

    def test_password_reset_unknown_email(self):
        resp = self.client.post(
            reverse("accounts:password_reset"),
            {"email": "unknown@test.com"},
            follow=False,
        )
        self.assertIn(resp.status_code, (200, 302))
        self.assertEqual(len(mail.outbox), 0)


class VerifyEmailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="verify@test.com", password="testpass123")
        self.user.email_verified = False
        self.user.save(update_fields=["email_verified"])
        self.factory = RequestFactory()

    def test_verify_email_valid_token(self):
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        from .tokens import email_verification_token

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = email_verification_token.make_token(self.user)
        request = self.factory.get(reverse("accounts:verify_email", args=[uid, token]))
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))
        resp = VerifyEmailView.as_view()(request, uidb64=uid, token=token)
        self.assertEqual(resp.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.assertIn(reverse("accounts:dashboard"), resp.url)

    def test_verify_email_invalid_token(self):
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        request = self.factory.get(reverse("accounts:verify_email", args=[uid, "bad-token"]))
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))
        resp = VerifyEmailView.as_view()(request, uidb64=uid, token="bad-token")
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)
