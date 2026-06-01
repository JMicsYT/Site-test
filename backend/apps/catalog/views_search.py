"""
Смарт-поиск с автодополнением для header-search.
Возвращает компактный JSON: товары + категории, с подсветкой совпадений на клиенте.
"""
from __future__ import annotations

from django.db.models import Q
from django.http import JsonResponse
from django.views import View

from .models import Category, Product


MAX_SUGGESTIONS = 8


class AutocompleteApiView(View):
    """GET /api/catalog/autocomplete/?q=...

    Возвращает: {"query": str, "products": [...], "categories": [...]}
    """

    def get(self, request):
        q = (request.GET.get("q") or "").strip()
        if len(q) < 2:
            return JsonResponse({"query": q, "products": [], "categories": []})

        products_qs = (
            Product.objects.filter(status="active")
            .filter(
                Q(name__icontains=q)
                | Q(short_description__icontains=q)
            )
            .select_related("category")
            .prefetch_related("media")
            .order_by("-created_at")[:MAX_SUGGESTIONS]
        )
        categories_qs = (
            Category.objects.filter(name__icontains=q)
            .order_by("sort_order", "name")[:4]
        )

        return JsonResponse({
            "query": q,
            "products": [
                {
                    "id": p.pk,
                    "name": p.name,
                    "url": f"/catalog/{p.slug}/",
                    "image": p.get_first_image_url() or "",
                    "price": str(p.final_price),
                    "has_discount": bool(p.has_discount),
                    "type": p.get_product_type_display(),
                    "category": p.category.name if p.category_id else "",
                }
                for p in products_qs
            ],
            "categories": [
                {
                    "id": c.pk,
                    "name": c.name,
                    "url": f"/catalog/?category={c.slug}",
                }
                for c in categories_qs
            ],
        })
