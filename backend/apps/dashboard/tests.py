from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.orders.models import Order
from apps.dashboard.views import CategoryEditView, DashboardView

User = get_user_model()


class DashboardAccessTests(TestCase):
    def test_dashboard_requires_staff(self):
        user = User.objects.create_user(email="user@test.com", password="pass")
        self.client.login(email="user@test.com", password="pass")
        resp = self.client.get(reverse("dashboard:index"))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/admin/login") or "login" in resp.url)

    def test_dashboard_staff_can_access(self):
        user = User.objects.create_user(email="staff@test.com", password="pass", is_staff=True)
        request = RequestFactory().get(reverse("dashboard:index"))
        request.user = user
        resp = DashboardView.as_view()(request)
        self.assertEqual(resp.status_code, 200)


class DashboardCategoryTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(email="staff@test.com", password="pass", is_staff=True)
        self.client.login(email="staff@test.com", password="pass")

    def test_create_category(self):
        resp = self.client.post(
            reverse("dashboard:category_new"),
            {"name": "Игры", "slug": "games", "description": "", "sort_order": 0},
            follow=False,
        )
        self.assertIn(resp.status_code, (200, 302))
        self.assertTrue(Category.objects.filter(slug="games").exists())

    def test_category_slug_validation(self):
        Category.objects.create(name="Existing", slug="existing")
        initial_count = Category.objects.count()
        request = RequestFactory().post(
            reverse("dashboard:category_new"),
            {"name": "New", "slug": "existing", "description": "", "sort_order": 0},
        )
        request.user = self.staff
        request.session = {}
        resp = CategoryEditView.as_view()(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Category.objects.count(), initial_count, "Дубликат слага не должен создавать категорию")


class DashboardProductTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(email="staff@test.com", password="pass", is_staff=True)
        self.cat = Category.objects.create(name="Cat", slug="cat")
        self.client.login(email="staff@test.com", password="pass")

    def test_create_product(self):
        resp = self.client.post(
            reverse("dashboard:product_new"),
            {
                "category": self.cat.pk,
                "name": "Test Product",
                "slug": "test-product",
                "short_description": "Short",
                "description": "Long",
                "price": "100",
                "product_type": "game",
                "license_type": "perpetual",
                "purpose": "personal",
                "status": "active",
            },
            follow=False,
        )
        self.assertIn(resp.status_code, (200, 302))
        self.assertTrue(Product.objects.filter(slug="test-product").exists())

    def test_product_price_negative(self):
        from apps.dashboard.views import ProductEditView

        request = RequestFactory().post(
            reverse("dashboard:product_new"),
            {
                "category": self.cat.pk,
                "name": "Bad",
                "slug": "bad",
                "short_description": "S",
                "description": "D",
                "price": "-10",
                "product_type": "game",
                "license_type": "perpetual",
                "purpose": "personal",
                "status": "active",
            },
        )
        request.user = self.staff
        request.session = {}
        resp = ProductEditView.as_view()(request)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Product.objects.filter(slug="bad").exists(), "Товар с отрицательной ценой не должен создаваться")


class DashboardOrderStatusTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(email="staff@test.com", password="pass", is_staff=True)
        self.user = User.objects.create_user(email="user@test.com", password="pass")
        self.order = Order.objects.create(
            user=self.user,
            amount=100,
            currency="RUB",
            status=Order.Status.PENDING,
        )
        self.client.login(email="staff@test.com", password="pass")

    def test_change_order_status(self):
        resp = self.client.post(
            reverse("dashboard:order_edit", args=[self.order.pk]),
            {"status": Order.Status.PAID},
            follow=False,
        )
        self.assertIn(resp.status_code, (200, 302))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)
