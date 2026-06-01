from django.conf import settings


def global_settings(request):
    # DEBUG в шаблоны не передаём — снижает риск утечки в проде
    return {
        "PROJECT_NAME": settings.PROJECT_NAME,
    }


def user_badges(request):
    """Счётчики для шапки сайта: избранное, сравнение, непрочитанные уведомления.

    Ничего не возвращает, если пользователь анонимный; экономит запросы к БД.
    """
    user = getattr(request, "user", None)
    data = {
        "favorites_count": 0,
        "compare_count": 0,
        "notifications_unread": 0,
        "compare_ids": [],
    }
    # Сравнение храним в сессии — оно доступно и анонимам
    try:
        session = getattr(request, "session", None)
        if session is not None:
            compare_ids = [int(x) for x in session.get("compare", []) if str(x).isdigit()]
            data["compare_ids"] = compare_ids
            data["compare_count"] = len(compare_ids)
    except Exception:
        pass
    if not (user and user.is_authenticated):
        return data
    try:
        from apps.favorites.models import Favorite
        fav_ids = list(
            Favorite.objects.filter(user=user).values_list("product_id", flat=True)
        )
        data["favorites_count"] = len(fav_ids)
        data["favorite_ids"] = fav_ids
    except Exception:
        pass
    try:
        from apps.notifications.models import Notification
        data["notifications_unread"] = Notification.objects.filter(
            user=user, is_read=False
        ).count()
    except Exception:
        pass
    return data


def recently_viewed(request):
    """
    Возвращает до 6 недавно просмотренных пользователем товаров.
    Хранятся в session['recently_viewed'] — список ID.
    """
    try:
        session = getattr(request, "session", None)
        if session is None:
            return {"recently_viewed_products": []}
        raw = session.get("recently_viewed") or []
        ids: list[int] = []
        for x in raw:
            try:
                v = int(x)
                if v > 0 and v not in ids:
                    ids.append(v)
            except (TypeError, ValueError):
                continue
        if not ids:
            return {"recently_viewed_products": []}
        from apps.catalog.models import Product
        products = list(
            Product.objects.filter(pk__in=ids[:6], status="active")
            .select_related("category")
            .prefetch_related("media")
        )
        order = {pk: i for i, pk in enumerate(ids)}
        products.sort(key=lambda p: order.get(p.pk, 999))
        return {"recently_viewed_products": products}
    except Exception:
        return {"recently_viewed_products": []}


def dashboard_counters(request):
    """Счётчики для сайдбара админки (только для staff)."""
    user = getattr(request, "user", None)
    if not (user and user.is_authenticated and user.is_staff):
        return {}
    # не падаем, если БД недоступна или модели ещё не мигрированы
    try:
        from apps.core.models import SupportTicket
        from apps.catalog.models import Review
        return {
            "sidebar_open_tickets": SupportTicket.objects.filter(
                status=SupportTicket.Status.OPEN
            ).count(),
            "sidebar_pending_reviews": Review.objects.filter(
                status=Review.Status.PENDING
            ).count(),
        }
    except Exception:
        return {}

