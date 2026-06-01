from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from apps.catalog.models import Product

from .models import Favorite


def _is_ajax(request) -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest" or \
        "application/json" in (request.headers.get("Accept") or "")


@method_decorator(login_required, name="dispatch")
class FavoriteToggleView(View):
    """POST — добавляет/удаляет товар из избранного текущего пользователя."""

    def post(self, request, product_id: int):
        product = get_object_or_404(Product, pk=product_id, status="active")
        fav, created = Favorite.objects.get_or_create(user=request.user, product=product)
        if not created:
            fav.delete()
            in_favorites = False
        else:
            in_favorites = True
        total = Favorite.objects.filter(user=request.user).count()
        if _is_ajax(request):
            return JsonResponse({
                "ok": True,
                "in_favorites": in_favorites,
                "count": total,
                "product_id": product.pk,
            })
        messages.success(
            request,
            "Добавлено в избранное." if in_favorites else "Удалено из избранного.",
        )
        return redirect(request.META.get("HTTP_REFERER") or "catalog:list")


@method_decorator(login_required, name="dispatch")
class FavoriteListView(View):
    """Страница «Мои избранные товары»."""
    template_name = "favorites/list.html"

    def get(self, request):
        favorites = (
            Favorite.objects
            .filter(user=request.user)
            .select_related("product", "product__category")
            .prefetch_related("product__media")
            .order_by("-created_at")
        )
        products = [f.product for f in favorites]
        return render(request, self.template_name, {"products": products, "total": len(products)})
