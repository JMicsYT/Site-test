import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key

# Каталог backend (родитель каталога shoshop)
_BACKEND_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = _BACKEND_DIR


def _load_env_file(path: Path) -> None:
    """Загрузить переменные из .env в os.environ (ручной парсинг, без python-dotenv)."""
    if not path.exists():
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if key and value and not key.startswith("#"):
                    # убрать кавычки вокруг значения
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
                        value = value[1:-1]
                    # Не затираем переменные, уже заданные Docker/compose (env_file)
                    if key not in os.environ:
                        os.environ[key] = value
    except Exception:
        pass


# Загрузка .env: python-dotenv, затем ручной парсинг если ключи БД не заданы
_env_candidates = [
    Path.cwd() / ".env",           # при запуске из backend или после chdir(backend)
    _BACKEND_DIR / ".env",
]
_in_docker = Path("/.dockerenv").exists()
try:
    from dotenv import load_dotenv
    for _p in _env_candidates:
        if _p.exists():
            # В Docker переменные из compose env_file не перезаписываем backend/.env
            load_dotenv(_p, override=not _in_docker)
            break
except ImportError:
    pass

# Локально: подгрузить .env вручную, если ключи БД не заданы (в Docker — только compose env_file)
if not _in_docker:
    _db_user = os.getenv("POSTGRES_USER")
    if not _db_user or _db_user == "shoshop":
        for _p in _env_candidates:
            _load_env_file(_p)
            if os.getenv("POSTGRES_USER") and os.getenv("POSTGRES_USER") != "shoshop":
                break


def env(key: str, default: str | None = None) -> str:
    return os.getenv(key, default) if os.getenv(key) is not None else default


SECRET_KEY = env("DJANGO_SECRET_KEY", get_random_secret_key())

DEBUG = env("DJANGO_DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "django_filters",
    # Local apps
    "apps.accounts",
    "apps.catalog",
    "apps.orders",
    "apps.payments",
    "apps.dashboard",
    "apps.core",
    "apps.favorites",
    "apps.promo",
    "apps.wallet",
    "apps.notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.LoginRateLimitMiddleware",
    "apps.core.middleware.ReferralCaptureMiddleware",
]

ROOT_URLCONF = "shoshop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.global_settings",
                "apps.core.context_processors.dashboard_counters",
                "apps.core.context_processors.user_badges",
                "apps.core.context_processors.recently_viewed",
            ],
        },
    },
]

WSGI_APPLICATION = "shoshop.wsgi.application"
ASGI_APPLICATION = "shoshop.asgi.application"


# ======================================================================
# БАЗА ДАННЫХ: только PostgreSQL.
# SQLite в проекте НЕ поддерживается ни в dev, ни в prod (требование диплома).
# Docker: POSTGRES_HOST=db, локально: POSTGRES_HOST=localhost.
# ======================================================================
_postgres_host = env("POSTGRES_HOST", "db")
# Локально без Docker имя «db» не резолвится — переключаемся на localhost.
# В контейнере НЕ подменяем: gethostbyname иногда падает, хотя Postgres доступен по имени db.
if _postgres_host == "db" and not _in_docker:
    import socket
    try:
        socket.gethostbyname("db")
    except socket.gaierror:
        _postgres_host = "localhost"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "shoshop"),
        "USER": env("POSTGRES_USER", "shoshop"),
        "PASSWORD": env("POSTGRES_PASSWORD", "shoshop"),
        "HOST": _postgres_host,
        "PORT": env("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": int(env("DB_CONN_MAX_AGE", "60")),
        "OPTIONS": {
            "connect_timeout": int(env("DB_CONNECT_TIMEOUT", "5")),
        },
    }
}

# Жёсткая защита от случайного SQLite: если кто-то переопределит ENGINE — упадём сразу.
assert DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql", (
    "Проект использует только PostgreSQL. SQLite не поддерживается."
)


AUTH_USER_MODEL = "accounts.User"


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "ru-ru"

TIME_ZONE = "Europe/Moscow"

USE_I18N = True

USE_TZ = True


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Кеш: по умолчанию локальный (для rate limit и кеша каталога)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "OPTIONS": {"MAX_ENTRIES": 10000},
    }
}
_cache_url = env("CACHE_URL", "")
if _cache_url:
    CACHES["default"] = {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": _cache_url,
    }

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "login": "10/min",
    },
}


# Письма: если задан EMAIL_HOST — используем SMTP, иначе консоль (для разработки)
_email_host = env("EMAIL_HOST", "")
if _email_host:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = _email_host
    EMAIL_PORT = int(env("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = env("EMAIL_USE_TLS", "true").lower() == "true"
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "no-reply@shoshop.local")

# Для ссылок в письмах (сброс пароля, подтверждение email)
DEFAULT_DOMAIN = env("DEFAULT_DOMAIN", "localhost")

# Требовать подтверждённый email для оформления заказов и добавления в корзину
REQUIRE_EMAIL_VERIFIED_FOR_PURCHASE = env("REQUIRE_EMAIL_VERIFIED_FOR_PURCHASE", "true").lower() == "true"


# ======================================================================
# CHANNELS (WebSocket)
# ======================================================================
# По умолчанию — InMemory (для dev/tests). В проде задайте CHANNELS_REDIS_URL.
_channels_redis_url = env("CHANNELS_REDIS_URL", "")
if _channels_redis_url:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [_channels_redis_url]},
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }


# ======================================================================
# TELEGRAM-УВЕДОМЛЕНИЯ АДМИНИСТРАТОРА
# ======================================================================
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_CHAT_ID = env("TELEGRAM_ADMIN_CHAT_ID", "")
TELEGRAM_NOTIFICATIONS_ENABLED = (
    env("TELEGRAM_NOTIFICATIONS_ENABLED", "false").lower() == "true"
    and bool(TELEGRAM_BOT_TOKEN) and bool(TELEGRAM_ADMIN_CHAT_ID)
)


# ======================================================================
# РЕФЕРАЛЬНАЯ ПРОГРАММА
# ======================================================================
# Сумма в рублях, которую получает пригласивший при первой оплате реферала.
REFERRAL_BONUS_AMOUNT = int(env("REFERRAL_BONUS_AMOUNT", "200"))
REFERRAL_SESSION_KEY = "ref_code"


CELERY_BROKER_URL = env("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"


# ======================================================================
# PRODUCTION HARDENING
# ======================================================================
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = int(env("SESSION_COOKIE_AGE", "1209600"))  # 2 недели
SESSION_EXPIRE_AT_BROWSER_CLOSE = env("SESSION_EXPIRE_AT_BROWSER_CLOSE", "false").lower() == "true"

# HSTS — форсируем HTTPS в продакшене
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_SSL_REDIRECT = env("DJANGO_SECURE_SSL_REDIRECT", "false").lower() == "true"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Защита от clickjacking (iframe)
X_FRAME_OPTIONS = "DENY"

# Поддержка reverse-proxy (nginx): определение HTTPS через заголовок
if env("SECURE_PROXY_SSL_HEADER", "").lower() == "true":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True


PROJECT_NAME = env("PROJECT_NAME", "ShoShop")

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "home"


LOGIN_RATE_LIMIT = int(env("LOGIN_RATE_LIMIT", "5"))
LOGIN_RATE_WINDOW = int(env("LOGIN_RATE_WINDOW", "300"))  # seconds


# ===== Безопасность: 2FA, HIBP, Account Lockout =====
HIBP_CHECK_ENABLED = env("HIBP_CHECK_ENABLED", "true").lower() == "true"

# Блокировка аккаунта после N неудачных попыток (в дополнение к IP rate-limit)
ACCOUNT_LOCKOUT_MAX_FAILURES = int(env("ACCOUNT_LOCKOUT_MAX_FAILURES", "10"))
ACCOUNT_LOCKOUT_DURATION = int(env("ACCOUNT_LOCKOUT_DURATION", "1800"))  # 30 минут

# Ключ для шифрования чувствительных полей (DigitalItem.value и т.п.).
# ВАЖНО: в проде генерируется один раз и хранится в секретном хранилище.
# Формат: Fernet URL-safe base64, 44 символа. Пустой — шифрование отключено.
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY", "")

# Секрет подписи одноразовых ссылок для скачивания цифровых товаров
DOWNLOAD_LINK_SECRET = env("DOWNLOAD_LINK_SECRET", SECRET_KEY)
DOWNLOAD_LINK_TTL = int(env("DOWNLOAD_LINK_TTL", "900"))  # 15 минут
DOWNLOAD_LINK_MAX_USES = int(env("DOWNLOAD_LINK_MAX_USES", "3"))

# CSP: по умолчанию включена, можно отключить ENV-переменной на переходный период
CSP_ENABLED = env("CSP_ENABLED", "true").lower() == "true"

# Callback: окно валидности timestamp в секундах
PAYMENT_CALLBACK_REPLAY_WINDOW = int(env("PAYMENT_CALLBACK_REPLAY_WINDOW", "300"))


PAYMENT_PROVIDER = {
    "PROVIDER_CLASS": env(
        "PAYMENT_PROVIDER_CLASS", "apps.payments.providers.StubPaymentProvider"
    ),
    "API_KEY": env("PAYMENT_API_KEY", ""),
    "API_SECRET": env("PAYMENT_API_SECRET", ""),
    "CALLBACK_URL": env("PAYMENT_CALLBACK_URL", "https://localhost/api/payments/callback/"),
    "CALLBACK_SECRET": env("PAYMENT_CALLBACK_SECRET", ""),
}

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "json": {
            "()": "apps.core.logging_formatter.JsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "security_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "security.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "json",
        },
        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "app.log"),
            "maxBytes": 20 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "json",
        },
    },
    "loggers": {
        "apps": {
            "level": "INFO",
            "handlers": ["console", "app_file"],
            "propagate": False,
        },
        "security": {
            "level": "INFO",
            "handlers": ["console", "security_file"],
            "propagate": False,
        },
    },
    "root": {
        "level": "WARNING",
        "handlers": ["console"],
    },
}

