from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from django.utils.http import urlsafe_base64_decode

from apps.core.audit import log_event
from apps.orders.models import Order, UserDigitalAccess

from .forms import (
    AvatarForm,
    LoginForm,
    PasswordChangeForm,
    ProfileForm,
    RegistrationForm,
)
from .models import User
from .tasks import send_email_verification, send_email_verification_sync
from .tokens import email_verification_token
from .views_twofa import TWOFA_SESSION_KEY


class RegisterView(View):
    template_name = "accounts/register.html"

    def get(self, request):
        form = RegistrationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
            except Exception:
                messages.error(request, "Не удалось выполнить регистрацию. Попробуйте ещё раз.")
                return render(request, self.template_name, {"form": form})

            # Реферальный код из сессии: связываем пользователя с пригласившим
            try:
                ref_key = getattr(settings, "REFERRAL_SESSION_KEY", "ref_code")
                ref_code = (request.session.get(ref_key) or "").strip()
                if ref_code:
                    inviter = (
                        User.objects
                        .filter(referral_code__iexact=ref_code)
                        .exclude(pk=user.pk)
                        .first()
                    )
                    if inviter is not None:
                        user.referred_by = inviter
                        user.save(update_fields=["referred_by"])
                    request.session.pop(ref_key, None)
                    request.session.modified = True
            except Exception:
                pass

            try:
                send_email_verification.delay(user.id)
            except Exception:
                send_email_verification_sync(user.id)
            log_event(
                "register", request=request, user=user,
                description="Новая регистрация",
            )
            messages.success(
                request,
                "Регистрация прошла успешно. На email отправлено письмо для подтверждения.",
            )
            login(request, user)
            return redirect("accounts:dashboard")
        return render(request, self.template_name, {"form": form})


class LoginView(View):
    """
    Логин с поддержкой:
    - account lockout (после N неудач временно блокируем)
    - 2FA (если включена — редирект на ввод кода)
    - защита от user enumeration (одинаковое сообщение для любой ошибки)
    """

    template_name = "accounts/login.html"
    GENERIC_LOGIN_ERROR = "Неверный email или пароль."

    def get(self, request):
        form = LoginForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        email = (request.POST.get("email") or "").strip().lower()

        user_obj = User.objects.filter(email=email).first() if email else None

        # Если пользователь временно заблокирован — не проверяем пароль вообще
        if user_obj and user_obj.is_locked():
            log_event(
                "login_failed", request=request, user=user_obj,
                description="Попытка входа в заблокированный аккаунт",
            )
            form.add_error(None, self.GENERIC_LOGIN_ERROR)
            return render(request, self.template_name, {"form": form})

        if form.is_valid():
            user = form.get_user()
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login_ip = _get_ip(request)
            user.last_login_ua = (request.META.get("HTTP_USER_AGENT") or "")[:512]
            user.save(update_fields=[
                "failed_login_attempts", "locked_until",
                "last_login_ip", "last_login_ua",
            ])

            if user.totp_enabled:
                request.session[TWOFA_SESSION_KEY] = user.pk
                log_event(
                    "login_success", request=request, user=user,
                    description="Шаг 1/2 пройден, ожидается TOTP",
                    meta={"step": "password_ok_awaiting_2fa"},
                )
                return redirect("accounts:twofa_verify")

            login(request, user)
            log_event(
                "login_success", request=request, user=user,
                description="Успешный вход (без 2FA)",
            )
            next_url = request.GET.get("next")
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect("accounts:dashboard")

        if user_obj:
            user_obj.failed_login_attempts = (user_obj.failed_login_attempts or 0) + 1
            max_failures = getattr(settings, "ACCOUNT_LOCKOUT_MAX_FAILURES", 10)
            if user_obj.failed_login_attempts >= max_failures:
                duration = getattr(settings, "ACCOUNT_LOCKOUT_DURATION", 1800)
                user_obj.locked_until = timezone.now() + timedelta(seconds=duration)
                user_obj.generate_unlock_token()
                user_obj.save(update_fields=[
                    "failed_login_attempts", "locked_until", "unlock_token",
                ])
                log_event(
                    "account_locked", request=request, user=user_obj,
                    description=f"Аккаунт заблокирован на {duration} сек",
                )
                try:
                    from .tasks import send_account_unlock_email_sync
                    send_account_unlock_email_sync(user_obj.id)
                except Exception:
                    pass
            else:
                user_obj.save(update_fields=["failed_login_attempts"])

        log_event(
            "login_failed", request=request, user=user_obj,
            description="Неуспешная попытка входа",
            meta={"email_tried": email[:254] if email else ""},
        )
        form.errors.clear()
        form.add_error(None, self.GENERIC_LOGIN_ERROR)
        return render(request, self.template_name, {"form": form})


def _get_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


@login_required
def logout_view(request):
    log_event("logout", request=request, user=request.user, description="Выход из системы")
    logout(request)
    messages.info(request, "Вы вышли из системы.")
    return redirect("home")


class AccountUnlockView(View):
    """Разблокировка аккаунта по ссылке из письма (unlock_token)."""

    def get(self, request, token: str):
        user = User.objects.filter(unlock_token=token).first() if token else None
        if not user:
            return render(request, "accounts/unlock_invalid.html", status=400)
        user.failed_login_attempts = 0
        user.locked_until = None
        user.unlock_token = ""
        user.save(update_fields=["failed_login_attempts", "locked_until", "unlock_token"])
        log_event(
            "account_unlocked", request=request, user=user,
            description="Пользователь разблокировал аккаунт по ссылке",
        )
        messages.success(request, "Аккаунт разблокирован. Теперь можно войти.")
        return redirect("accounts:login")


class VerifyEmailView(View):
    template_name = "accounts/verify_email.html"

    def get(self, request, uidb64, token):
        from .models import User

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except Exception:
            user = None

        if user is not None and email_verification_token.check_token(user, token):
            user.email_verified = True
            user.save(update_fields=["email_verified"])
            log_event(
                "email_verified", request=request, user=user,
                description="Email подтверждён",
            )
            messages.success(request, "Email успешно подтверждён.")
            return redirect("accounts:dashboard")

        return render(request, self.template_name, {"invalid": True})


@method_decorator(login_required, name="dispatch")
class ResendVerifyEmailView(View):
    """Повторная отправка письма для подтверждения email."""

    def post(self, request):
        try:
            send_email_verification.delay(request.user.id)
        except Exception:
            send_email_verification_sync(request.user.id)
        messages.success(request, "Письмо с ссылкой для подтверждения отправлено на ваш email.")
        return redirect("accounts:dashboard")


@method_decorator(login_required, name="dispatch")
class DashboardView(View):
    template_name = "accounts/dashboard.html"

    def get(self, request):
        orders_qs = (
            Order.objects.filter(user=request.user)
            .select_related("user")
            .prefetch_related("items__product")
            .order_by("-created_at")
        )
        accesses = (
            UserDigitalAccess.objects.filter(user=request.user)
            .select_related("product", "digital_item")
            .order_by("-purchased_at")
        )

        stats_agg = orders_qs.aggregate(
            total_count=Count("id"),
            paid_sum=Sum("amount", filter=Q(status="paid")),
        )
        paid_count = orders_qs.filter(status="paid").count()
        access_count = accesses.count()

        stats = {
            "orders_total": stats_agg["total_count"] or 0,
            "orders_paid": paid_count,
            "spent_total": stats_agg["paid_sum"] or 0,
            "access_total": access_count,
        }

        return render(
            request,
            self.template_name,
            {
                "orders": orders_qs[:5],
                "accesses": accesses[:5],
                "stats": stats,
            },
        )


@method_decorator(login_required, name="dispatch")
class ProfileEditView(View):
    template_name = "accounts/profile_edit.html"

    def get(self, request):
        form = ProfileForm(instance=request.user)
        avatar_form = AvatarForm(instance=request.user)
        return render(
            request,
            self.template_name,
            {"form": form, "avatar_form": avatar_form},
        )

    def post(self, request):
        if "avatar" in request.FILES or request.POST.get("form") == "avatar":
            avatar_form = AvatarForm(request.POST, request.FILES, instance=request.user)
            if avatar_form.is_valid():
                avatar_form.save()
                messages.success(request, "Аватар обновлён.")
                return redirect("accounts:profile_edit")
            form = ProfileForm(instance=request.user)
            return render(
                request,
                self.template_name,
                {"form": form, "avatar_form": avatar_form},
            )

        if request.POST.get("remove_avatar"):
            if request.user.avatar:
                request.user.avatar.delete(save=False)
                request.user.avatar = None
                request.user.save(update_fields=["avatar"])
                messages.success(request, "Аватар удалён.")
            return redirect("accounts:profile_edit")

        form = ProfileForm(request.POST, instance=request.user)
        avatar_form = AvatarForm(instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль обновлён.")
            return redirect("accounts:profile_edit")
        return render(
            request,
            self.template_name,
            {"form": form, "avatar_form": avatar_form},
        )


@method_decorator(login_required, name="dispatch")
class PasswordChangeView(View):
    template_name = "accounts/password_change.html"

    def _security_context(self, request):
        from apps.core.models import SecurityEvent
        events = (
            SecurityEvent.objects
            .filter(user=request.user)
            .order_by("-created_at")[:10]
        )
        return {"recent_events": events}

    def get(self, request):
        form = PasswordChangeForm(user=request.user)
        ctx = {"form": form, **self._security_context(request)}
        return render(request, self.template_name, ctx)

    def post(self, request):
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            log_event(
                "password_change", request=request, user=request.user,
                description="Пользователь сменил пароль",
            )
            messages.success(request, "Пароль успешно изменён.")
            return redirect("accounts:dashboard")
        ctx = {"form": form, **self._security_context(request)}
        return render(request, self.template_name, ctx)


@method_decorator(login_required, name="dispatch")
class OrderListView(View):
    """Отдельная страница «Мои заказы» в ЛК."""

    template_name = "accounts/order_list.html"

    def get(self, request):
        orders = (
            Order.objects.filter(user=request.user)
            .select_related("user")
            .prefetch_related("items__product")
            .order_by("-created_at")
        )
        return render(request, self.template_name, {"orders": orders})

