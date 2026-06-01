from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.orders.models import Order
from apps.orders.services import apply_payment_result


User = get_user_model()


class OrderFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", password="testpass123")
        self.user.email_verified = True
        self.user.save(update_fields=["email_verified"])
        cat = Category.objects.create(name="Игры", slug="games")
        self.product = Product.objects.create(
            category=cat,
            name="Test Game",
            slug="test-game",
            short_description="Short",
            description="Long",
            price=100,
            product_type="game",
            license_type="perpetual",
            purpose="personal",
            status="active",
        )

    def test_create_and_pay_order(self):
        self.client.login(email="user@example.com", password="testpass123")
        resp = self.client.post(reverse("orders:checkout", args=[self.product.id]))
        # В заглушке происходит редирект на внешний URL
        self.assertEqual(resp.status_code, 302)
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.amount, self.product.price)
        apply_payment_result(order, status="success", transaction_id="TX-1")
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.transaction_id, "TX-1")

