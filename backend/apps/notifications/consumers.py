"""WebSocket-consumer для push-уведомлений авторизованных пользователей."""
from __future__ import annotations

import json

try:
    from channels.generic.websocket import AsyncJsonWebsocketConsumer
except ImportError:  # pragma: no cover
    AsyncJsonWebsocketConsumer = object  # type: ignore


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """Каждому авторизованному пользователю — своя группа user_{id}."""

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return
        self.group_name = f"user_{user.pk}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"type": "hello", "user_id": user.pk})

    async def disconnect(self, code):
        group = getattr(self, "group_name", None)
        if group:
            try:
                await self.channel_layer.group_discard(group, self.channel_name)
            except Exception:
                pass

    async def receive_json(self, content, **kwargs):
        # Клиент может отправлять ping; отвечаем pong.
        if isinstance(content, dict) and content.get("type") == "ping":
            await self.send_json({"type": "pong"})

    async def notify(self, event):
        """Хэндлер группового события type='notify'."""
        await self.send_json({"type": "notification", "data": event.get("payload") or {}})
