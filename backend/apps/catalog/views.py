from decimal import Decimal, InvalidOperation

from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Prefetch, Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View
from rest_framework import filters, viewsets
from rest_framework.pagination import PageNumberPagination

from .models import Category, Product, Review
from .serializers import CategorySerializer, ProductSerializer


class ProductPagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = "page_size"
    max_page_size = 100

CATALOG_PAGE_SIZE = 24


class CatalogListView(View):
    template_name = "catalog/list.html"

    def _parse_decimal(self, raw):
        if raw in (None, ""):
            return None
        try:
            return Decimal(str(raw).replace(",", "."))
        except (InvalidOperation, ValueError):
            return None

    def get(self, request):
        categories = cache.get("catalog_categories")
        if categories is None:
            categories = list(Category.objects.order_by("sort_order", "name"))
            cache.set("catalog_categories", categories, 300)

        # Границы цены для слайдера (по всей активной базе)
        price_bounds = cache.get("catalog_price_bounds")
        if price_bounds is None:
            from django.db.models import Max, Min
            aggr = Product.objects.filter(status="active").aggregate(
                lo=Min("price"), hi=Max("price"),
            )
            lo = aggr.get("lo") or Decimal("0")
            hi = aggr.get("hi") or Decimal("10000")
            price_bounds = {"min": int(lo), "max": int(hi) or 10000}
            cache.set("catalog_price_bounds", price_bounds, 300)

        qs = (
            Product.objects.filter(status="active")
            .select_related("category")
            .prefetch_related("media")
            .annotate(
                _avg_rating=Avg(
                    "reviews__rating",
                    filter=Q(reviews__status=Review.Status.PUBLISHED),
                ),
                _reviews_count=Count(
                    "reviews",
                    filter=Q(reviews__status=Review.Status.PUBLISHED),
                ),
            )
        )

        category_slug = request.GET.get("category")
        product_type = request.GET.get("type")
        license_type = request.GET.get("license")
        purpose = request.GET.get("purpose")
        q = (request.GET.get("q") or "").strip()
        ordering = request.GET.get("ordering", "-created_at")
        min_price = self._parse_decimal(request.GET.get("min_price"))
        max_price = self._parse_decimal(request.GET.get("max_price"))
        only_discount = request.GET.get("discount") == "1"
        only_new = request.GET.get("new") == "1"
        min_rating_raw = request.GET.get("rating")

        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if product_type:
            qs = qs.filter(product_type=product_type)
        if license_type:
            qs = qs.filter(license_type=license_type)
        if purpose:
            qs = qs.filter(purpose=purpose)
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(short_description__icontains=q)
                | Q(description__icontains=q)
            )
        if min_price is not None:
            qs = qs.filter(price__gte=min_price)
        if max_price is not None:
            qs = qs.filter(price__lte=max_price)
        if only_discount:
            qs = qs.filter(discount_price__isnull=False, discount_price__gt=0)
        if only_new:
            from datetime import timedelta
            qs = qs.filter(created_at__gte=timezone.now() - timedelta(days=14))
        if min_rating_raw:
            try:
                min_rating = int(min_rating_raw)
                if 1 <= min_rating <= 5:
                    qs = qs.filter(_avg_rating__gte=min_rating)
            except (TypeError, ValueError):
                pass

        allowed_orderings = {
            "-created_at": "-created_at",
            "created_at": "created_at",
            "price": "price",
            "-price": "-price",
            "rating": "-_avg_rating",
            "popular": "-_reviews_count",
        }
        qs = qs.order_by(allowed_orderings.get(ordering, "-created_at"))

        paginator = Paginator(qs, CATALOG_PAGE_SIZE)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)
        query_copy = request.GET.copy()
        query_copy.pop("page", None)
        pagination_query = query_copy.urlencode()

        # Для AJAX-обновления грида возвращаем партиал
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return render(
                request,
                "catalog/_grid_partial.html",
                {
                    "page_obj": page_obj,
                    "products": page_obj,
                    "paginator": paginator,
                    "pagination_query": pagination_query,
                },
            )

        return render(
            request,
            self.template_name,
            {
                "page_obj": page_obj,
                "products": page_obj,
                "categories": categories,
                "paginator": paginator,
                "pagination_query": pagination_query,
                "price_min": price_bounds["min"],
                "price_max": price_bounds["max"],
                "cur_min_price": min_price if min_price is not None else price_bounds["min"],
                "cur_max_price": max_price if max_price is not None else price_bounds["max"],
                "cur_only_discount": only_discount,
                "cur_only_new": only_new,
                "cur_min_rating": min_rating_raw or "",
            },
        )


class ProductDetailView(View):
    template_name = "catalog/detail.html"

    def get(self, request, slug):
        product = get_object_or_404(
            Product.objects.select_related("category").prefetch_related(
                "media",
                Prefetch(
                    "reviews",
                    queryset=(
                        Review.objects
                        .filter(status=Review.Status.PUBLISHED)
                        .select_related("user")
                        .order_by("-created_at")
                    ),
                ),
            ),
            slug=slug,
            status="active",
        )
        related = (
            Product.objects.filter(
                status="active", category=product.category
            )
            .exclude(id=product.id)
            .prefetch_related("media")
            .order_by("-created_at")[:4]
        )

        # Отзывы: можно ли пользователю оставить отзыв
        from .forms import ReviewForm
        from .views_review import _user_owns_product
        can_review = False
        already_reviewed = False
        review_form = None
        if request.user.is_authenticated:
            already_reviewed = Review.objects.filter(
                product=product, user=request.user
            ).exists()
            if not already_reviewed and _user_owns_product(request.user, product):
                can_review = True
                review_form = ReviewForm()

        # Сохраняем ID в «недавно просмотренные» (сессия)
        try:
            rv = list(request.session.get("recently_viewed") or [])
            rv = [int(x) for x in rv if str(x).isdigit() and int(x) != product.pk]
            rv.insert(0, product.pk)
            request.session["recently_viewed"] = rv[:12]
            request.session.modified = True
        except Exception:
            pass

        return render(
            request,
            self.template_name,
            {
                "product": product,
                "related": related,
                "can_review": can_review,
                "already_reviewed": already_reviewed,
                "review_form": review_form,
            },
        )


class CategoryListView(View):
    """Страница со всеми категориями (обзор)."""
    template_name = "catalog/categories.html"

    def get(self, request):
        categories = (
            Category.objects.annotate(
                product_count=Count("products", filter=Q(products__status="active"))
            )
            .order_by("sort_order", "name")
        )
        return render(request, self.template_name, {"categories": categories})


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by("sort_order", "name")
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Product.objects.filter(status="active")
        .select_related("category")
        .prefetch_related("media")
        .order_by("-created_at")
    )
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "short_description", "description"]
    ordering_fields = ["price", "created_at"]

