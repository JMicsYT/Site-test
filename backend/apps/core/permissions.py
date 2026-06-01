"""Миксины для view, связанные с контролем доступа."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404


class OwnerRequiredMixin(LoginRequiredMixin):
    """
    Проверка «пользователь = владелец объекта».
    Подкласс должен определить .get_object() (например, через DetailView или явно).
    Атрибут owner_field указывает, какое поле содержит владельца (по умолчанию 'user').
    """

    owner_field = "user"
    raise_404_for_strangers = True  # отдаём 404 вместо 403 — не раскрываем существование объекта

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        obj = self.get_object()
        if obj is None:
            raise Http404
        owner = getattr(obj, self.owner_field, None)
        if owner is None or owner.pk != request.user.pk:
            if self.raise_404_for_strangers:
                raise Http404
            raise PermissionDenied("Нет доступа к этому объекту")
        self.object = obj
        return super().dispatch(request, *args, **kwargs)
