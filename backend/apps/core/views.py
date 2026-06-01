from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from apps.catalog.models import Product


def health_view(request):
    """Health-check для оркестрации: проверка БД, при ошибке — 503."""
    try:
        connection.ensure_connection()
        return JsonResponse({"status": "ok"}, status=200)
    except Exception:
        return JsonResponse({"status": "error", "detail": "database"}, status=503)


def about_view(request):
    """Страница «О платформе»: для кого, о платформе, поддержка."""
    return render(request, "core/about.html")


def page_not_found(request, exception=None):
    return render(request, "404.html", status=404)


def server_error(request):
    return render(request, "500.html", status=500)


_DEFAULT_TERMS = """
1. Общие положения
ShoShop — цифровой маркетплейс, предоставляющий доступ к цифровым товарам (игры, ПО, курсы, медиа, цифровые ключи и коды).
Регистрируясь на платформе и/или оформляя заказ, пользователь принимает условия настоящего Соглашения.

2. Предмет Соглашения
Платформа обеспечивает оформление заказов, приём оплаты и выдачу цифровых товаров после подтверждения оплаты.

3. Цифровые товары
После оплаты доступ к цифровому товару становится доступен в личном кабинете. Товары выдаются одноразовыми защищёнными ссылками с ограниченным сроком действия.
Возврат средств за цифровые товары, к которым пользователь получил доступ, не осуществляется, за исключением случаев, предусмотренных законодательством РФ (в т.ч. Закон «О защите прав потребителей», ст. 26.1).

4. Обязанности пользователя
Пользователь обязуется: предоставлять достоверные данные при регистрации, не передавать учётные данные третьим лицам, не использовать платформу для распространения вредоносного ПО и действий, нарушающих законодательство.

5. Ответственность
Платформа не несёт ответственности за действия третьих лиц, а также за работоспособность продуктов, являющихся предметом сделки с третьими правообладателями.

6. Порядок разрешения споров
Все споры подлежат досудебному урегулированию. В случае недостижения согласия — споры рассматриваются в суде по месту нахождения платформы.

7. Изменение Соглашения
Администрация вправе в одностороннем порядке изменять условия. Продолжение использования платформы означает согласие с новой редакцией.
"""


_DEFAULT_PRIVACY = """
1. Оператор персональных данных
ООО «ShoShop» (далее — Оператор) обрабатывает персональные данные пользователей в соответствии с Федеральным законом №152-ФЗ «О персональных данных».

2. Цели обработки
- Регистрация и идентификация пользователя;
- Оформление и исполнение заказов;
- Информирование пользователя о статусе заказа, обновлениях и акциях (при наличии согласия);
- Обеспечение безопасности платформы (в т.ч. ведение аудит-журналов в целях защиты от несанкционированного доступа).

3. Состав обрабатываемых данных
email, имя, фамилия, телефон (опционально), адрес (опционально), IP-адрес, User-Agent, история заказов, сведения о действиях в аккаунте (для аудит-журнала).

4. Правовые основания
Согласие субъекта персональных данных (при регистрации), договорные обязательства (для исполнения заказов), законные интересы Оператора (обеспечение безопасности).

5. Передача третьим лицам
Данные передаются платёжным системам и сервисам доставки только в объёме, необходимом для исполнения заказа. Данные не передаются в рекламных целях третьим лицам без согласия пользователя.

6. Хранение и безопасность
Данные хранятся на серверах в РФ. Применяются меры защиты:
- передача по HTTPS (TLS);
- хеширование паролей (алгоритмы Django, PBKDF2-SHA256);
- симметричное шифрование цифровых ключей в БД (Fernet AES-128);
- двухфакторная аутентификация (TOTP) — по желанию пользователя;
- аудит-журнал действий пользователя и администраторов.

7. Права пользователя
Пользователь вправе запросить доступ к своим данным, их уточнение, блокирование или уничтожение, отозвать согласие на обработку. Запросы направляются по адресу, указанному в контактах.

8. Cookies
Используются сессионные и технические cookie (авторизация, CSRF). Аналитические cookie не используются без согласия.

9. Изменение политики
Актуальная редакция Политики опубликована на сайте. Продолжение использования платформы означает согласие с новой редакцией.
"""


def terms_view(request):
    from .models import SiteSetting
    text = SiteSetting.get("terms_of_use") or _DEFAULT_TERMS
    return render(request, "core/legal.html", {"title": "Пользовательское соглашение", "content": text})


def privacy_view(request):
    from .models import SiteSetting
    text = SiteSetting.get("privacy_policy") or _DEFAULT_PRIVACY
    return render(request, "core/legal.html", {"title": "Политика конфиденциальности", "content": text})


@method_decorator(login_required, name="dispatch")
class SupportChatApiView(View):
    """API для виджета поддержки: GET — данные чата, POST — отправить сообщение."""

    def get(self, request):
        from datetime import timedelta
        from django.utils import timezone
        from .models import SupportTicket

        # 1) Актуальный открытый тикет — показываем его
        ticket = (
            SupportTicket.objects.filter(user=request.user, status=SupportTicket.Status.OPEN)
            .order_by("-updated_at")
            .first()
        )
        # 2) Если открытого нет — показываем последний завершённый
        #    за последние 7 дней, чтобы пользователь увидел ответ админа и статус.
        if not ticket:
            cutoff = timezone.now() - timedelta(days=7)
            ticket = (
                SupportTicket.objects.filter(
                    user=request.user,
                    status=SupportTicket.Status.COMPLETED,
                    updated_at__gte=cutoff,
                )
                .order_by("-updated_at")
                .first()
            )
        if not ticket:
            return JsonResponse({"ticket_id": None, "status": None, "messages": []})

        messages = [
            {
                "id": m.id,
                "body": m.body,
                "created_at": m.created_at.isoformat(),
                "is_staff": m.author.is_staff,
                "author": m.author.email if m.author.is_staff else None,
            }
            for m in ticket.messages.select_related("author").order_by("created_at")
        ]
        return JsonResponse({
            "ticket_id": ticket.id,
            "status": ticket.status,
            "messages": messages,
        })

    def post(self, request):
        from .models import SupportTicket, SupportMessage

        ticket_id = request.POST.get("ticket_id")
        body = (request.POST.get("body") or "").strip()
        if not body or len(body) > 5000:
            return JsonResponse({"ok": False, "error": "Введите сообщение (до 5000 символов)."}, status=400)

        if ticket_id:
            ticket = SupportTicket.objects.filter(
                user=request.user, pk=ticket_id, status=SupportTicket.Status.OPEN
            ).first()
        else:
            ticket = None

        if not ticket:
            ticket = SupportTicket.objects.create(user=request.user, status=SupportTicket.Status.OPEN)

        SupportMessage.objects.create(ticket=ticket, author=request.user, body=body)
        return JsonResponse({"ok": True, "ticket_id": ticket.id})


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        from django.core.cache import cache
        from django.db.models import Count, Q
        from apps.catalog.models import Category

        ctx = super().get_context_data(**kwargs)
        cache_key = "home_ctx_v2"
        data = cache.get(cache_key)
        if data is None:
            popular = list(
                Product.objects.filter(status="active")
                .prefetch_related("media")
                .order_by("-created_at")[:8]
            )
            featured = list(
                Product.objects.filter(status="active", is_featured=True)
                .prefetch_related("media")
                .order_by("-created_at")[:4]
            )
            categories = list(
                Category.objects.annotate(
                    product_count=Count("products", filter=Q(products__status="active"))
                )
                .filter(product_count__gt=0)
                .order_by("sort_order", "name")[:8]
            )
            stats = {
                "products": Product.objects.filter(status="active").count(),
                "categories": Category.objects.count(),
            }
            try:
                from apps.accounts.models import User as _U
                stats["clients"] = _U.objects.filter(is_active=True).count()
            except Exception:
                stats["clients"] = 0

            data = {
                "popular": popular,
                "featured": featured,
                "categories": categories,
                "stats": stats,
            }
            cache.set(cache_key, data, 300)

        ctx.update({
            "popular_products": data["popular"],
            "featured_products": data["featured"],
            "home_categories": data["categories"],
            "home_stats": data["stats"],
        })
        return ctx

