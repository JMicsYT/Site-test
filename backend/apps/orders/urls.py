from django.urls import path
from django.views.generic import RedirectView

from .views import (
    AddToCartView,
    CartApplyCouponView,
    CartCheckoutView,
    CartToggleWalletView,
    CartView,
    CheckoutView,
    OrderCancelView,
    OrderPayView,
    RemoveFromCartView,
    RequestDownloadLinkView,
    RevealDigitalItemView,
    UpdateCartView,
)

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="accounts:order_list", permanent=False), name="list"),
    path("checkout/<int:product_id>/", CheckoutView.as_view(), name="checkout"),
    path("<int:order_id>/cancel/", OrderCancelView.as_view(), name="cancel"),
    path("<int:order_id>/pay/", OrderPayView.as_view(), name="pay"),
    path("digital/<int:access_id>/link/", RequestDownloadLinkView.as_view(), name="digital_link"),
    path("digital/reveal/", RevealDigitalItemView.as_view(), name="digital_reveal"),
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/add/<int:product_id>/", AddToCartView.as_view(), name="add_to_cart"),
    path("cart/update/<int:product_id>/", UpdateCartView.as_view(), name="cart_update"),
    path("cart/remove/<int:product_id>/", RemoveFromCartView.as_view(), name="cart_remove"),
    path("cart/checkout/", CartCheckoutView.as_view(), name="cart_checkout"),
    path("cart/apply-coupon/", CartApplyCouponView.as_view(), name="cart_apply_coupon"),
    path("cart/toggle-wallet/", CartToggleWalletView.as_view(), name="cart_toggle_wallet"),
]

