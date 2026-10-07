from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Store
from .models import Product


class RoleAccessTests(TestCase):
    def setUp(self):
        self.a = Store.objects.create(name="Central")
        self.b = Store.objects.create(name="Norte")
        User = get_user_model()
        self.admin = User.objects.create_user(username="admin", email="admin@test.local", password="Test2026!", role=User.Role.ADMIN)
        self.manager = User.objects.create_user(username="manager", email="manager@test.local", password="Test2026!", role=User.Role.MANAGER, store=self.a)
        self.sales = User.objects.create_user(username="sales", email="sales@test.local", password="Test2026!", role=User.Role.SALES, store=self.a)
        self.auditor = User.objects.create_user(username="auditor", email="auditor@test.local", password="Test2026!", role=User.Role.AUDITOR)
        self.product_a = Product.objects.create(code="A-1", name="Laptop A", store=self.a, category="computadoras", price=Decimal("100"), stock=10)
        self.product_b = Product.objects.create(code="B-1", name="Laptop B", store=self.b, category="computadoras", price=Decimal("200"), stock=20)

    def verified_login(self, user):
        self.client.force_login(user)
        session = self.client.session
        session["mfa_verified_user_id"] = user.pk
        session.save()

    def test_manager_sees_own_store_and_cannot_change_other(self):
        self.verified_login(self.manager)
        response = self.client.get(reverse("inventory:list"))
        self.assertContains(response, "Laptop A")
        self.assertNotContains(response, "Laptop B")
        self.assertEqual(self.client.get(reverse("inventory:edit", args=[self.product_b.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("inventory:delete", args=[self.product_b.pk])).status_code, 403)
        self.assertTrue(Product.objects.filter(pk=self.product_b.pk).exists())

    def test_sales_can_update_own_stock_but_not_price(self):
        self.verified_login(self.sales)
        self.assertEqual(self.client.get(reverse("inventory:edit", args=[self.product_a.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("inventory:stock", args=[self.product_b.pk]), {"stock": 4}).status_code, 404)
        self.client.post(reverse("inventory:stock", args=[self.product_a.pk]), {"stock": 4, "price": "1"})
        self.product_a.refresh_from_db()
        self.assertEqual(self.product_a.stock, 4)
        self.assertEqual(self.product_a.price, Decimal("100"))

    def test_auditor_reads_all_without_mutation(self):
        self.verified_login(self.auditor)
        self.assertContains(self.client.get(reverse("inventory:list")), "Laptop B")
        self.assertEqual(self.client.get(reverse("inventory:reports")).status_code, 200)
        self.assertEqual(self.client.post(reverse("inventory:delete", args=[self.product_a.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("inventory:stock", args=[self.product_a.pk]), {"stock": 0}).status_code, 403)

    def test_admin_can_manage_users_and_all_products(self):
        self.verified_login(self.admin)
        self.assertEqual(self.client.get(reverse("team")).status_code, 200)
        self.assertContains(self.client.get(reverse("inventory:list")), "Laptop B")
        self.assertEqual(self.client.post(reverse("inventory:delete", args=[self.product_b.pk])).status_code, 302)
        self.assertFalse(Product.objects.filter(pk=self.product_b.pk).exists())

    def test_health_and_mfa_gate(self):
        self.assertEqual(self.client.get(reverse("inventory:health")).json()["status"], "ok")
        self.client.force_login(self.manager)
        self.assertRedirects(self.client.get(reverse("inventory:list")), reverse("mfa"))
