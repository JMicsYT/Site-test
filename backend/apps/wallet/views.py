"""Публичная страница кошелька пользователя: баланс + история операций."""
from __future__ import annotations

from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from .models import get_or_create_wallet


@method_decorator(login_required, name="dispatch")
class WalletView(View):
    template_name = "wallet/index.html"

    def get(self, request):
        wallet = get_or_create_wallet(request.user)
        qs = wallet.transactions.select_related("order").order_by("-created_at")
        paginator = Paginator(qs, 20)
        page = paginator.get_page(request.GET.get("page"))

        income = sum(
            (t.amount for t in qs if t.amount and t.amount > 0),
            Decimal("0"),
        )
        outcome = sum(
            (t.amount for t in qs if t.amount and t.amount < 0),
            Decimal("0"),
        )

        return render(
            request,
            self.template_name,
            {
                "wallet": wallet,
                "transactions": page,
                "page_obj": page,
                "paginator": paginator,
                "income_total": income,
                "outcome_total": abs(outcome),
            },
        )
