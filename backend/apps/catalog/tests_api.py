from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product


User = get_user_model()


class CatalogApiTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Софт", slug="software")
        Product.objects.create(
            category=cat,
            name="Test Software",
            slug="test-software",
            short_description="Short",
            description="Long",
            price=500,
            product_type="software",
            license_type="subscription",
            purpose="business",
            status="active",
        )

    def test_products_list_api(self):
        url = reverse("product-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        results = data.get("results", data) if isinstance(data, dict) else data
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Test Software")

