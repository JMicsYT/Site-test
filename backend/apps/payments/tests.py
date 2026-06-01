from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings

from apps.catalog.models import Category, Product
from apps.orders.models import Order, OrderItem, UserDigitalAccess
from apps.payments.api_urls import PaymentCallbackView

User = get_user_model()


def _payment_provider(secret=""):
    base = getattr(settings, "PAYMENT_PROVIDER", {}) or {}
    return {**base, "CALLBACK_SECRET": secret}


class PaymentCallbackTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="u@t.com", password="pass")
        cat = Category.objects.create(name="Cat", slug="cat")
        self.product = Product.objects.create(
            category=cat,
            name="P",
            slug="p",
            short_description="S",
            description="D",
            price=100,
            product_type="game",
            license_type="perpetual",
            purpose="personal",
            status="active",
        )
        self.factory = RequestFactory()

    def _call_callback(self, order_id, status="success", transaction_id="T1", secret_header=None):
        request = self.factory.post(
            "/api/payments/callback/",
            data={"order_id": order_id, "status": status, "transaction_id": transaction_id},
        )
        if secret_header is not None:
            request.META["HTTP_X_PAYMENT_SECRET"] = secret_header
        return PaymentCallbackView.as_view()(request)

    @override_settings(PAYMENT_PROVIDER=_payment_provider(""))
    def test_callback_creates_notification(self):
        order = Order.objects.create(
            user=self.user,
            amount=100,
            currency="RUB",
            status=Order.Status.PENDING,
        )
        resp = self._call_callback(order.pk)
        self.assertEqual(resp.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)

    @override_settings(PAYMENT_PROVIDER=_payment_provider("secret123"))
    def test_callback_403_without_secret(self):
        order = Order.objects.create(
            user=self.user,
            amount=100,
            currency="RUB",
            status=Order.Status.PENDING,
        )
        resp = self._call_callback(order.pk, secret_header=None)
        self.assertEqual(resp.status_code, 403)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)

    @override_settings(PAYMENT_PROVIDER=_payment_provider("secret123"))
    def test_callback_200_with_secret_header(self):
        order = Order.objects.create(
            user=self.user,
            amount=100,
            currency="RUB",
            status=Order.Status.PENDING,
        )
        resp = self._call_callback(order.pk, secret_header="secret123")
        self.assertEqual(resp.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)

    @override_settings(PAYMENT_PROVIDER=_payment_provider("secret123"))
    def test_callback_idempotency(self):
        order = Order.objects.create(
            user=self.user,
            amount=100,
            currency="RUB",
            status=Order.Status.PENDING,
        )
        OrderItem.objects.create(order=order, product=self.product, price=100, quantity=1)
        resp1 = self._call_callback(order.pk, secret_header="secret123")
        self.assertEqual(resp1.status_code, 200)
        resp2 = self._call_callback(order.pk, transaction_id="T2", secret_header="secret123")
        self.assertEqual(resp2.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        count_by_user_product = UserDigitalAccess.objects.filter(user=self.user, product=self.product).count()
        self.assertLessEqual(count_by_user_product, 1, "Повторный callback не должен дублировать выдачу")
