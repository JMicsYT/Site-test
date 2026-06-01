"""
ASGI-приложение для ShoShop.

Поддерживает:
- HTTP-трафик Django (как обычно)
- WebSocket-трафик Django Channels (уведомления, чат поддержки в будущем)
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shoshop.settings")

# Django должен быть инициализирован до импорта Channels-консьюмеров
django_asgi_app = get_asgi_application()

try:
    from channels.auth import AuthMiddlewareStack
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.security.websocket import AllowedHostsOriginValidator

    from apps.notifications.routing import websocket_urlpatterns as notify_ws

    application = ProtocolTypeRouter(
        {
            "http": django_asgi_app,
            "websocket": AllowedHostsOriginValidator(
                AuthMiddlewareStack(URLRouter(notify_ws))
            ),
        }
    )
except Exception:  # noqa: BLE001
    # В dev без channels — просто HTTP
    application = django_asgi_app
