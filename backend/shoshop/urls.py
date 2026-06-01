from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.catalog.views_compare import CompareClearView, CompareToggleView, CompareView
from apps.core.views import HomeView, about_view, health_view, privacy_view, terms_view


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_view, name="health"),
    path("", HomeView.as_view(), name="home"),
    path("about/", about_view, name="about"),
    path("terms/", terms_view, name="terms"),
    path("privacy/", privacy_view, name="privacy"),
    path("accounts/", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    path("catalog/", include(("apps.catalog.urls", "catalog"), namespace="catalog")),
    path("orders/", include(("apps.orders.urls", "orders"), namespace="orders")),
    path("dashboard/", include(("apps.dashboard.urls", "dashboard"), namespace="dashboard")),
    path("favorites/", include("apps.favorites.urls")),
    path("compare/", CompareView.as_view(), name="compare"),
    path("compare/toggle/<int:product_id>/", CompareToggleView.as_view(), name="compare_toggle"),
    path("compare/clear/", CompareClearView.as_view(), name="compare_clear"),
    path("support/", include("apps.core.support_urls")),
    path("api/accounts/", include("apps.accounts.api_urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("wallet/", include("apps.wallet.urls")),
    path("api/catalog/", include("apps.catalog.api_urls")),
    path("api/orders/", include("apps.orders.api_urls")),
    path("api/payments/", include("apps.payments.api_urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = "apps.core.views.page_not_found"
handler500 = "apps.core.views.server_error"

