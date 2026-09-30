from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Product


class InventoryFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", password="safe-test-pass-123")

    def test_login_is_required_and_full_crud_persists(self):
        self.assertRedirects(self.client.get(reverse("inventory:list")), "/login/?next=/")
        self.assertTrue(self.client.login(username="tester", password="safe-test-pass-123"))
        response = self.client.post(reverse("inventory:create"), {
            "code": " p-01 ", "name": "Monitor de prueba", "category": "monitores",
            "description": "", "price": "89.50", "stock": "8",
        })
        self.assertRedirects(response, reverse("inventory:list"))
        product = Product.objects.get(code="P-01")
        self.assertContains(self.client.get(reverse("inventory:list")), "Stock bajo")
        response = self.client.post(reverse("inventory:edit", args=[product.pk]), {
            "code": "P-01", "name": "Monitor actualizado", "category": "monitores",
            "description": "", "price": "99.50", "stock": "12",
        })
        self.assertRedirects(response, reverse("inventory:list"))
        product.refresh_from_db()
        self.assertEqual(product.name, "Monitor actualizado")
        self.assertEqual(product.price, Decimal("99.50"))
        self.assertEqual(product.stock_status, "Disponible")
        self.assertEqual(self.client.get(reverse("inventory:delete", args=[product.pk])).status_code, 405)
        self.assertRedirects(self.client.post(reverse("inventory:delete", args=[product.pk])), reverse("inventory:list"))
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())

    def test_invalid_product_and_health(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("inventory:create"), {
            "code": "P-02", "name": "Cable", "category": "perifericos",
            "description": "", "price": "-1", "stock": "-3",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(self.client.get(reverse("inventory:health")).json()["status"], "ok")
