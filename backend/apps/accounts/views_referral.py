"""Страница реферальной программы для пользователя."""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View


@method_decorator(login_required, name="dispatch")
class ReferralView(View):
    template_name = "accounts/referral.html"

    def get(self, request):
        user = request.user
        user.ensure_referral_code()
        if not user.referral_code:
            user.save(update_fields=["referral_code"])

        host = request.get_host()
        scheme = "https" if request.is_secure() else "http"
        ref_link = f"{scheme}://{host}/?ref={user.referral_code}"

        referrals = (
            user.referrals.all()
            .order_by("-date_joined")
            .only("id", "email", "date_joined", "referral_bonus_paid")
        )
        paid_count = referrals.filter(referral_bonus_paid=True).count()
        bonus_amount = Decimal(getattr(settings, "REFERRAL_BONUS_AMOUNT", 0) or 0)
        total_earned = bonus_amount * paid_count

        return render(
            request,
            self.template_name,
            {
                "ref_code": user.referral_code,
                "ref_link": ref_link,
                "bonus_amount": bonus_amount,
                "referrals": referrals,
                "paid_count": paid_count,
                "total_earned": total_earned,
            },
        )
