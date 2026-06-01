"""
2FA: включение/отключение, проверка кода при входе.
"""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from apps.core.audit import log_event

from .models import User
from .security import (
    build_totp_uri,
    consume_backup_code,
    generate_backup_codes,
    generate_totp_secret,
    qr_png_data_uri,
    verify_totp,
)


TWOFA_SESSION_KEY = "pending_2fa_user_id"
TWOFA_SESSION_REMEMBER = "pending_2fa_remember"


@method_decorator(login_required, name="dispatch")
class TwoFactorSetupView(View):
    """Включение 2FA: показываем QR + просим ввести код для подтверждения."""

    template_name = "accounts/twofa_setup.html"

    def get(self, request):
        if request.user.totp_enabled:
            messages.info(request, "Двухфакторная аутентификация уже включена.")
            return redirect("accounts:dashboard")

        secret = request.session.get("pending_totp_secret")
        if not secret:
            secret = generate_totp_secret()
            request.session["pending_totp_secret"] = secret

        uri = build_totp_uri(request.user.email, secret)
        return render(
            request,
            self.template_name,
            {
                "secret": secret,
                "qr_data_uri": qr_png_data_uri(uri),
                "otpauth_uri": uri,
            },
        )

    def post(self, request):
        if request.user.totp_enabled:
            return redirect("accounts:dashboard")

        secret = request.session.get("pending_totp_secret", "")
        code = (request.POST.get("code") or "").strip()

        if not verify_totp(secret, code):
            messages.error(request, "Неверный код. Попробуйте ещё раз.")
            return redirect("accounts:twofa_setup")

        plain_codes, hashed_codes = generate_backup_codes()
        request.user.totp_secret = secret
        request.user.totp_enabled = True
        request.user.backup_codes = hashed_codes
        request.user.save(
            update_fields=["totp_secret", "totp_enabled", "backup_codes"]
        )
        request.session.pop("pending_totp_secret", None)

        log_event(
            "twofa_enabled",
            request=request,
            user=request.user,
            description="Пользователь включил 2FA",
        )
        messages.success(
            request, "Двухфакторная аутентификация включена. Сохраните резервные коды!"
        )
        return render(
            request,
            "accounts/twofa_backup_codes.html",
            {"codes": plain_codes},
        )


@method_decorator(login_required, name="dispatch")
class TwoFactorDisableView(View):
    """Отключение 2FA: требует ввести текущий TOTP-код."""

    template_name = "accounts/twofa_disable.html"

    def get(self, request):
        if not request.user.totp_enabled:
            return redirect("accounts:dashboard")
        return render(request, self.template_name)

    def post(self, request):
        if not request.user.totp_enabled:
            return redirect("accounts:dashboard")
        code = (request.POST.get("code") or "").strip()
        if not verify_totp(request.user.totp_secret, code):
            log_event(
                "twofa_failed",
                request=request,
                user=request.user,
                description="Неверный код при отключении 2FA",
            )
            messages.error(request, "Неверный код.")
            return redirect("accounts:twofa_disable")

        request.user.totp_enabled = False
        request.user.totp_secret = ""
        request.user.backup_codes = []
        request.user.save(update_fields=["totp_secret", "totp_enabled", "backup_codes"])
        log_event(
            "twofa_disabled",
            request=request,
            user=request.user,
            description="Пользователь отключил 2FA",
        )
        messages.success(request, "Двухфакторная аутентификация отключена.")
        return redirect("accounts:dashboard")


class TwoFactorVerifyView(View):
    """
    Промежуточный шаг логина: пользователь ввёл email+пароль корректно,
    в сессии сохранён pending_2fa_user_id — теперь нужен TOTP-код.
    """

    template_name = "accounts/twofa_verify.html"

    def get(self, request):
        if not request.session.get(TWOFA_SESSION_KEY):
            return redirect("accounts:login")
        return render(request, self.template_name)

    def post(self, request):
        uid = request.session.get(TWOFA_SESSION_KEY)
        if not uid:
            return redirect("accounts:login")
        try:
            user = User.objects.get(pk=uid, is_active=True, totp_enabled=True)
        except User.DoesNotExist:
            request.session.pop(TWOFA_SESSION_KEY, None)
            return redirect("accounts:login")

        code = (request.POST.get("code") or "").strip()
        use_backup = bool(request.POST.get("use_backup"))

        ok = False
        if use_backup:
            matched, new_codes = consume_backup_code(user.backup_codes or [], code)
            if matched:
                user.backup_codes = new_codes
                user.save(update_fields=["backup_codes"])
                ok = True
        else:
            ok = verify_totp(user.totp_secret, code)

        if not ok:
            log_event(
                "twofa_failed",
                request=request,
                user=user,
                description="Неверный TOTP/backup при входе",
                meta={"use_backup": use_backup},
            )
            messages.error(request, "Неверный код. Попробуйте ещё раз.")
            return redirect("accounts:twofa_verify")

        request.session.pop(TWOFA_SESSION_KEY, None)
        auth_login(request, user)
        log_event(
            "login_success",
            request=request,
            user=user,
            description="Успешный вход (2FA пройдена)",
            meta={"method": "backup" if use_backup else "totp"},
        )
        return redirect("accounts:dashboard")
