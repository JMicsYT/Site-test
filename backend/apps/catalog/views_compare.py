"""
Сравнение товаров. ID выбранных товаров хранятся в сессии (доступно и анонимам).
Лимит — 4 товара. Возвращает JSON для AJAX-тоггла.
"""
from __future__ import annotations

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .models import Product

COMPARE_SESSION_KEY = "compare"
COMPARE_MAX = 4


def _get_ids(request) -> list[int]:
    raw = request.session.get(COMPARE_SESSION_KEY) or []
    ids: list[int] = []
    for x in raw:
        try:
            v = int(x)
            if v > 0 and v not in ids:
                ids.append(v)
        except (TypeError, ValueError):
            continue
    return ids[:COMPARE_MAX]


def _save_ids(request, ids: list[int]) -> None:
    request.session[COMPARE_SESSION_KEY] = ids[:COMPARE_MAX]
    request.session.modified = True


def _is_ajax(request) -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest" or \
        "application/json" in (request.headers.get("Accept") or "")


class CompareToggleView(View):
    """POST — добавить/убрать товар из сравнения (сессии)."""

    def post(self, request, product_id: int):
        product = get_object_or_404(Product, pk=product_id, status="active")
        ids = _get_ids(request)
        overflow = False
        if product.pk in ids:
            ids = [x for x in ids if x != product.pk]
            in_compare = False
        else:
            if len(ids) >= COMPARE_MAX:
                overflow = True
                in_compare = product.pk in ids
            else:
                ids.append(product.pk)
                in_compare = True
        _save_ids(request, ids)
        if _is_ajax(request):
            return JsonResponse({
                "ok": True,
                "in_compare": in_compare,
                "count": len(ids),
                "overflow": overflow,
                "product_id": product.pk,
            })
        return redirect(request.META.get("HTTP_REFERER") or "catalog:list")


class CompareView(View):
    """Страница сравнения товаров: таблица характеристик side-by-side."""
    template_name = "catalog/compare.html"

    def get(self, request):
        ids = _get_ids(request)
        products = list(
            Product.objects
            .filter(pk__in=ids, status="active")
            .select_related("category")
            .prefetch_related("media")
        )
        # Сортируем в том же порядке, что и в сессии
        order = {pk: i for i, pk in enumerate(ids)}
        products.sort(key=lambda p: order.get(p.pk, 999))
        rows = [
            ("Категория", lambda p: p.category.name if p.category_id else "—"),
            ("Тип", lambda p: p.get_product_type_display()),
            ("Лицензия", lambda p: p.get_license_type_display()),
            ("Назначение", lambda p: p.get_purpose_display()),
            ("Цена", lambda p: f"{p.final_price} ₽"),
            ("Скидка", lambda p: f"−{p.discount_percent}%" if p.has_discount else "—"),
            ("Рейтинг", lambda p: f"{p.avg_rating:.1f} ({p.reviews_count})" if p.reviews_count else "—"),
            ("Новинка", lambda p: "Да" if p.is_new else "—"),
        ]
        rendered_rows = [
            {"label": label, "cells": [fn(p) for p in products]}
            for label, fn in rows
        ]
        return render(
            request,
            self.template_name,
            {"products": products, "rows": rendered_rows},
        )


class CompareClearView(View):
    def post(self, request):
        _save_ids(request, [])
        return redirect("compare")
