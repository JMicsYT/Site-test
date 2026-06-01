from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import permissions, viewsets

from apps.catalog.models import Product
from apps.core.audit import log_event
from apps.core.models import DownloadAudit
from apps.payments.providers import get_payment_provider
from .downloads import (
    generate_signed_token,
    get_client_ip,
    parse_signed_token,
    register_use,
)
from .models import Order, UserDigitalAccess
from .serializers import OrderSerializer
from .services import create_order_for_user


def _require_email_verified(request):
    """Если включено требование подтверждения email и пользователь не подтвердил — редирект с сообщением."""
    if not getattr(settings, "REQUIRE_EMAIL_VERIFIED_FOR_PURCHASE", False):
        return None
    if getattr(request.user, "email_verified", True):
        return None
    messages.error(
        request,
        "Для оформления заказов необходимо подтвердить email. Проверьте почту или запросите письмо повторно.",
    )
    return redirect("accounts:dashboard")


@method_decorator(login_required, name="dispatch")
class CheckoutView(View):
    """
    Покупка одного товара по его ID. При REQUIRE_EMAIL_VERIFIED_FOR_PURCHASE требуется подтверждённый email.
    """

    def post(self, request, product_id):
        redirect_resp = _require_email_verified(request)
        if redirect_resp:
            return redirect_resp
        product = get_object_or_404(Product, pk=product_id, status="active")
        order = Order.objects.create(
            user=request.user,
            amount=product.price,
            currency="RUB",
        )
        order.items.create(product=product, price=product.price, quantity=1)

        provider = get_payment_provider()
        init_result = provider.init_payment(order)
        order.status = Order.Status.PENDING
        order.transaction_id = init_result.provider_reference
        order.save(update_fields=["status", "transaction_id"])
        return redirect(init_result.redirect_url)


@method_decorator(login_required, name="dispatch")
class OrdersListView(View):
    template_name = "orders/list.html"

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
        return render(request, self.template_name, {"orders": orders})


@method_decorator(login_required, name="dispatch")
class OrderCancelView(View):
    """Пользователь отменяет свой заказ, который ещё не оплачен."""

    def post(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        if order.status not in (Order.Status.CREATED, Order.Status.PENDING):
            messages.error(request, "Этот заказ нельзя отменить.")
            return redirect("accounts:order_list")
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Заказ #{order.pk} отменён.")
        return redirect("accounts:order_list")


@method_decorator(login_required, name="dispatch")
class OrderPayView(View):
    """Повторно инициирует оплату заказа и редиректит на платёжного провайдера."""

    def post(self, request, order_id):
        redirect_resp = _require_email_verified(request)
        if redirect_resp:
            return redirect_resp
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        if order.status not in (Order.Status.CREATED, Order.Status.PENDING):
            messages.error(request, "Этот заказ уже нельзя оплатить.")
            return redirect("accounts:order_list")
        provider = get_payment_provider()
        init_result = provider.init_payment(order)
        order.status = Order.Status.PENDING
        order.transaction_id = init_result.provider_reference
        order.save(update_fields=["status", "transaction_id", "updated_at"])
        return redirect(init_result.redirect_url)


@method_decorator(login_required, name="dispatch")
class CartView(View):
    template_name = "orders/cart.html"

    def get(self, request):
        from decimal import Decimal
        from apps.promo.services import find_coupon, validate_for_user, CouponError

        cart = request.session.get("cart", {})
        product_ids = []
        for pid in cart.keys():
            try:
                product_ids.append(int(pid))
            except (TypeError, ValueError):
                continue
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids, status="active")}
        items = []
        total = Decimal("0")
        for pid, qty in cart.items():
            try:
                pid_int = int(pid)
                qty = max(0, min(int(qty), CART_MAX_QTY))
            except (TypeError, ValueError):
                continue
            if qty <= 0:
                continue
            product = products.get(pid_int)
            if not product:
                continue
            subtotal = Decimal(product.final_price) * qty
            total += subtotal
            items.append({"product": product, "qty": qty, "subtotal": subtotal})

        coupon_code = (request.session.get("cart_coupon_code") or "").strip()
        coupon = None
        coupon_error = None
        coupon_discount = Decimal("0")
        if coupon_code:
            c = find_coupon(coupon_code)
            if not c:
                coupon_error = "Такого промокода не существует."
            else:
                try:
                    validate_for_user(c, request.user, total)
                    coupon = c
                    coupon_discount = c.compute_discount(total)
                except CouponError as e:
                    coupon_error = str(e)

        use_wallet = bool(request.session.get("cart_use_wallet"))
        wallet_balance = Decimal("0")
        wallet_apply = Decimal("0")
        try:
            from apps.wallet.models import get_or_create_wallet
            w = get_or_create_wallet(request.user)
            wallet_balance = w.balance or Decimal("0")
        except Exception:
            pass

        final_total = (total - coupon_discount).quantize(Decimal("0.01"))
        if use_wallet and wallet_balance > 0 and final_total > 0:
            wallet_apply = min(wallet_balance, final_total)
            final_total = (final_total - wallet_apply).quantize(Decimal("0.01"))

        return render(
            request,
            self.template_name,
            {
                "items": items,
                "total": total,
                "coupon_code": coupon_code,
                "coupon": coupon,
                "coupon_error": coupon_error,
                "coupon_discount": coupon_discount,
                "use_wallet": use_wallet,
                "wallet_balance": wallet_balance,
                "wallet_apply": wallet_apply,
                "final_total": final_total,
            },
        )


@method_decorator(login_required, name="dispatch")
class CartApplyCouponView(View):
    """POST: code=... — сохранить промокод в сессии (или очистить если пусто)."""

    def post(self, request):
        code = (request.POST.get("code") or "").strip()
        if code:
            request.session["cart_coupon_code"] = code
            messages.info(request, f"Промокод «{code}» применён к корзине.")
        else:
            request.session.pop("cart_coupon_code", None)
            messages.info(request, "Промокод снят.")
        request.session.modified = True
        return redirect("orders:cart")


@method_decorator(login_required, name="dispatch")
class CartToggleWalletView(View):
    """POST — включает/выключает использование баланса в корзине."""

    def post(self, request):
        use = request.POST.get("use") == "1"
        request.session["cart_use_wallet"] = use
        request.session.modified = True
        return redirect("orders:cart")


CART_MAX_QTY = 99


@method_decorator(login_required, name="dispatch")
class AddToCartView(View):
    def post(self, request, product_id):
        redirect_resp = _require_email_verified(request)
        if redirect_resp:
            return redirect_resp
        product = get_object_or_404(Product, pk=product_id, status="active")
        cart = request.session.get("cart", {})
        key = str(product.id)
        current = cart.get(key, 0)
        try:
            current = int(current)
        except (TypeError, ValueError):
            current = 0
        cart[key] = min(current + 1, CART_MAX_QTY)
        request.session["cart"] = cart
        messages.success(request, f"Товар «{product.name}» добавлен в корзину.")
        return redirect("orders:cart")


@method_decorator(login_required, name="dispatch")
class UpdateCartView(View):
    """Изменить количество товара в корзине (POST qty=1..99)."""

    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id, status="active")
        try:
            qty = int(request.POST.get("qty", 1))
        except (TypeError, ValueError):
            qty = 1
        qty = max(0, min(qty, CART_MAX_QTY))
        cart = request.session.get("cart", {})
        key = str(product.id)
        if qty <= 0:
            cart.pop(key, None)
        else:
            cart[key] = qty
        request.session["cart"] = cart
        messages.success(request, "Корзина обновлена.")
        return redirect("orders:cart")


@method_decorator(login_required, name="dispatch")
class RemoveFromCartView(View):
    """Удалить товар из корзины."""

    def post(self, request, product_id):
        cart = request.session.get("cart", {})
        cart.pop(str(product_id), None)
        request.session["cart"] = cart
        messages.success(request, "Товар удалён из корзины.")
        return redirect("orders:cart")


@method_decorator(login_required, name="dispatch")
class CartCheckoutView(View):
    def post(self, request):
        from decimal import Decimal
        from apps.promo.services import (
            CouponError, find_coupon, validate_for_user,
        )

        redirect_resp = _require_email_verified(request)
        if redirect_resp:
            return redirect_resp
        cart = request.session.get("cart", {})
        if not cart:
            return redirect("orders:cart")
        products_with_qty = []
        for pid, qty in cart.items():
            try:
                pid_int = int(pid)
                qty = int(qty)
                if pid_int > 0 and 0 < qty <= CART_MAX_QTY:
                    products_with_qty.append((pid_int, qty))
            except (TypeError, ValueError):
                continue
        if not products_with_qty:
            return redirect("orders:cart")

        # Применяем промокод, если он есть и валиден
        coupon = None
        coupon_code = (request.session.get("cart_coupon_code") or "").strip()
        if coupon_code:
            c = find_coupon(coupon_code)
            if c:
                # Для предварительной валидации нужна сумма. Посчитаем быстро.
                total = Decimal("0")
                products = {p.id: p for p in Product.objects.filter(
                    id__in=[pid for pid, _ in products_with_qty], status="active"
                )}
                for pid, qty in products_with_qty:
                    prod = products.get(pid)
                    if prod:
                        total += Decimal(prod.final_price) * qty
                try:
                    validate_for_user(c, request.user, total)
                    coupon = c
                except CouponError as e:
                    messages.error(request, str(e))
                    return redirect("orders:cart")

        # Флаг «использовать баланс»
        wallet_apply = None
        if request.session.get("cart_use_wallet"):
            try:
                from apps.wallet.models import get_or_create_wallet
                w = get_or_create_wallet(request.user)
                wallet_apply = w.balance or Decimal("0")
            except Exception:
                wallet_apply = None

        try:
            order = create_order_for_user(
                request.user, products_with_qty,
                coupon=coupon, wallet_apply=wallet_apply,
            )
        except ValueError:
            return redirect("orders:cart")

        # Если баланс полностью покрыл заказ — сразу проводим его как оплаченный.
        if order.amount <= 0:
            from .services import apply_payment_result
            apply_payment_result(order, "success", transaction_id=f"wallet-{order.pk}")
            messages.success(request, f"Заказ #{order.pk} оплачен с баланса.")
            request.session["cart"] = {}
            request.session.pop("cart_coupon_code", None)
            request.session.pop("cart_use_wallet", None)
            return redirect("accounts:order_list")

        provider = get_payment_provider()
        init_result = provider.init_payment(order)
        order.status = Order.Status.PENDING
        order.transaction_id = init_result.provider_reference
        order.save(update_fields=["status", "transaction_id"])
        request.session["cart"] = {}
        request.session.pop("cart_coupon_code", None)
        request.session.pop("cart_use_wallet", None)
        return redirect(init_result.redirect_url)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by("-created_at")


# ======================================================================
# Безопасная выдача цифрового товара: одноразовые подписанные ссылки.
# ======================================================================

@method_decorator(login_required, name="dispatch")
class RequestDownloadLinkView(View):
    """
    Пользователь кликает «Получить ссылку» — мы генерируем подписанный токен
    и редиректим на страницу раскрытия значения.
    """

    def post(self, request, access_id: int):
        access = get_object_or_404(
            UserDigitalAccess, pk=access_id, user=request.user
        )
        if not access.can_redownload and access.digital_item is None:
            messages.error(request, "Повторная выдача отключена для этого товара.")
            return redirect("accounts:dashboard")

        token = generate_signed_token(access.pk, request.user.pk)
        log_event(
            "digital_download", request=request, user=request.user,
            description="Сгенерирована одноразовая ссылка",
            meta={"access_id": access.pk, "product_id": access.product_id},
        )
        url = reverse("orders:digital_reveal") + f"?t={token}"
        return redirect(url)

    def get(self, request, access_id: int):
        return HttpResponseNotAllowed(["POST"])


@method_decorator(login_required, name="dispatch")
class RevealDigitalItemView(View):
    """
    Показывает plain-значение цифрового товара по подписанному одноразовому токену.
    Проверки:
      - подпись и TTL токена (TimestampSigner);
      - owner: user_id из токена == request.user.pk;
      - лимит использований по jti (кеш);
      - существование access + digital_item.

    Каждое обращение (успех/отказ) пишется в DownloadAudit.
    """

    template_name = "orders/digital_reveal.html"

    def get(self, request):
        token = request.GET.get("t", "")
        parsed = parse_signed_token(token)

        if not parsed:
            DownloadAudit.objects.create(
                user=request.user, access_id=0, product_id=0,
                ip_address=get_client_ip(request),
                user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:512],
                success=False, reason="invalid_or_expired_token",
            )
            log_event(
                "digital_download", request=request, user=request.user,
                description="Попытка использования недействительного токена",
                meta={"reason": "invalid_or_expired_token"},
            )
            raise Http404

        if parsed["user_id"] != request.user.pk:
            DownloadAudit.objects.create(
                user=request.user, access_id=parsed["access_id"], product_id=0,
                token_jti=parsed["jti"],
                ip_address=get_client_ip(request),
                user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:512],
                success=False, reason="user_mismatch",
            )
            log_event(
                "suspicious_activity", request=request, user=request.user,
                description="Чужой токен скачивания",
                meta={"token_user_id": parsed["user_id"]},
            )
            raise Http404

        access = (
            UserDigitalAccess.objects
            .select_related("product", "digital_item")
            .filter(pk=parsed["access_id"], user=request.user)
            .first()
        )
        if not access:
            raise Http404

        allowed, uses = register_use(parsed["jti"])
        if not allowed:
            DownloadAudit.objects.create(
                user=request.user, access_id=access.pk, product_id=access.product_id,
                digital_item_id=access.digital_item_id, token_jti=parsed["jti"],
                ip_address=get_client_ip(request),
                user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:512],
                success=False, reason="max_uses_exceeded",
            )
            return render(
                request, "orders/digital_reveal_expired.html", status=410
            )

        plain = ""
        if access.digital_item:
            plain = access.digital_item.plain_value

        DownloadAudit.objects.create(
            user=request.user, access_id=access.pk, product_id=access.product_id,
            digital_item_id=access.digital_item_id, token_jti=parsed["jti"],
            ip_address=get_client_ip(request),
            user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:512],
            success=True,
        )
        log_event(
            "digital_download", request=request, user=request.user,
            description="Показано значение цифрового товара",
            meta={
                "access_id": access.pk,
                "product_id": access.product_id,
                "uses": uses,
                "jti": parsed["jti"],
            },
        )

        return render(
            request,
            self.template_name,
            {
                "access": access,
                "plain_value": plain,
                "uses": uses,
                "max_uses": int(getattr(settings, "DOWNLOAD_LINK_MAX_USES", 3)),
            },
        )

