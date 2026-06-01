from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View

from .models import Notification


@method_decorator(login_required, name="dispatch")
class NotificationListApiView(View):
    """GET JSON — последние 20 уведомлений + счётчик непрочитанных."""

    def get(self, request):
        qs = Notification.objects.filter(user=request.user).order_by("-created_at")
        items = [n.to_dict() for n in qs[:20]]
        unread = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({"items": items, "unread": unread})


@method_decorator(login_required, name="dispatch")
class MarkAllReadApiView(View):
    def post(self, request):
        updated = Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True)
        return JsonResponse({"ok": True, "updated": updated})


@method_decorator(login_required, name="dispatch")
class MarkReadApiView(View):
    def post(self, request, pk: int):
        updated = Notification.objects.filter(
            pk=pk, user=request.user, is_read=False
        ).update(is_read=True)
        return JsonResponse({"ok": True, "updated": updated})
