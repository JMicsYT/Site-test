import time

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect


class SecurityHeadersMiddleware:
    """
    Добавляет заголовки безопасности к каждому ответу:
    - X-Content-Type-Options: nosniff (A05 Security Misconfiguration)
    - Referrer-Policy: strict-origin-when-cross-origin (privacy)
    - Permissions-Policy: отключаем опасные API
    - Content-Security-Policy: защита от XSS (A03 Injection)
    - Cross-Origin-*-Policy: изоляция контекста
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _build_csp(self) -> str:
        # 'unsafe-inline' для style/script оставляем только потому, что в шаблонах
        # и виджетах используются inline-стили/скрипты. Для полноценного запрета
        # inline нужно вынести их в файлы и добавить nonce — это следующий шаг.
        directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "img-src 'self' data: blob: https:",
            "font-src 'self' data: https://fonts.gstatic.com",
            "connect-src 'self' ws: wss:",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "base-uri 'self'",
            "object-src 'none'",
        ]
        return "; ".join(directives)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if not getattr(response, "_security_headers_applied", False):
            response["X-Content-Type-Options"] = "nosniff"
            response["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response["Permissions-Policy"] = (
                "geolocation=(), microphone=(), camera=(), payment=(), usb=()"
            )
            response["X-XSS-Protection"] = "1; mode=block"
            response["Cross-Origin-Opener-Policy"] = "same-origin"
            response["Cross-Origin-Resource-Policy"] = "same-origin"
            if getattr(settings, "CSP_ENABLED", True):
                response["Content-Security-Policy"] = self._build_csp()
            response._security_headers_applied = True
        return response


class ReferralCaptureMiddleware:
    """
    Перехватывает GET-запросы с параметром ?ref=CODE и сохраняет код
    в сессии, чтобы использовать при регистрации (поле User.referred_by).
    """

    SESSION_KEY_DEFAULT = "ref_code"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method == "GET":
            code = (request.GET.get("ref") or "").strip()
            if code:
                key = getattr(settings, "REFERRAL_SESSION_KEY", self.SESSION_KEY_DEFAULT)
                try:
                    if request.session.get(key) != code:
                        request.session[key] = code[:16].upper()
                        request.session.modified = True
                except Exception:
                    pass
        return self.get_response(request)


class LoginRateLimitMiddleware:
    """
    Ограничение попыток логина по IP+username.
    При превышении — редирект на страницу входа с сообщением (не JSON).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method != "POST":
            return self.get_response(request)

        path = request.path
        # Ограничение: логин, регистрация, сброс пароля
        if "login" in path:
            username = request.POST.get("email") or request.POST.get("username") or "anonymous"
            cache_key = f"rate_login:{self._get_ip(request)}:{username}"
            redirect_target = "accounts:login"
            msg = "Слишком много попыток входа. Попробуйте через несколько минут."
        elif "register" in path:
            username = request.POST.get("email", "") or "anonymous"
            cache_key = f"rate_register:{self._get_ip(request)}:{username}"
            redirect_target = "accounts:register"
            msg = "Слишком много попыток регистрации. Попробуйте позже."
        elif "password-reset" in path and "done" not in path:
            username = request.POST.get("email", "") or "anonymous"
            cache_key = f"rate_pwdreset:{self._get_ip(request)}:{username}"
            redirect_target = "accounts:password_reset"
            msg = "Слишком много запросов сброса пароля. Попробуйте позже."
        else:
            return self.get_response(request)

        ip = self._get_ip(request)
        data = cache.get(cache_key, {"count": 0, "ts": time.time()})
        window = getattr(settings, "LOGIN_RATE_WINDOW", 300)
        limit = getattr(settings, "LOGIN_RATE_LIMIT", 5)

        now = time.time()
        if now - data["ts"] > window:
            data = {"count": 0, "ts": now}

        if data["count"] >= limit:
            messages.error(request, msg)
            return redirect(redirect_target)

        data["count"] += 1
        cache.set(cache_key, data, window)

        return self.get_response(request)

    @staticmethod
    def _get_ip(request: HttpRequest) -> str:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

