"""Добавление отзывов покупателями. Только для тех, кто купил товар."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View

from apps.core.audit import log_event

from .forms import ReviewForm
from .models import Product, Review


def _user_owns_product(user, product: Product) -> bool:
    """Проверяет: пользователь оплачивал заказ с этим товаром."""
    from apps.orders.models import Order
    return Order.objects.filter(
        user=user,
        status=Order.Status.PAID,
        items__product=product,
    ).exists()


@method_decorator(login_required, name="dispatch")
class ReviewCreateView(View):
    """POST /catalog/<slug>/review/ — создать отзыв (на модерации)."""

    def post(self, request, slug: str):
        product = get_object_or_404(Product, slug=slug, status="active")

        if not _user_owns_product(request.user, product):
            messages.error(
                request,
                "Оставить отзыв можно только после покупки товара.",
            )
            return redirect("catalog:detail", slug=product.slug)

        if Review.objects.filter(product=product, user=request.user).exists():
            messages.info(request, "Вы уже оставляли отзыв на этот товар.")
            return redirect("catalog:detail", slug=product.slug)

        form = ReviewForm(request.POST)
        if not form.is_valid():
            for err in form.errors.values():
                messages.error(request, "; ".join(err))
            return redirect("catalog:detail", slug=product.slug)

        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.status = Review.Status.PENDING
        review.save()

        log_event(
            "review_created",
            request=request,
            user=request.user,
            description=f"Отзыв на товар #{product.pk} (рейтинг {review.rating})",
        )
        messages.success(
            request,
            "Спасибо за отзыв! Он появится на сайте после проверки модератором.",
        )
        return redirect("catalog:detail", slug=product.slug)
