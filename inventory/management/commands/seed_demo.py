import os
import secrets
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import Store
from inventory.models import Product


SAMPLES = [
    ("TEC-001", "Laptop Pro 14", "computadoras", Decimal("3299.00"), 18, "Equipo portátil de 14 pulgadas"),
    ("TEC-002", "Monitor Ultra 27", "monitores", Decimal("1099.00"), 7, "Monitor de alta resolución"),
    ("TEC-003", "Teclado Mecánico", "perifericos", Decimal("279.00"), 32, "Teclado compacto"),
    ("TEC-004", "Mouse Inalámbrico", "perifericos", Decimal("129.00"), 42, "Mouse ergonómico"),
    ("TEC-005", "SSD NVMe 1 TB", "componentes", Decimal("379.00"), 9, "Unidad de almacenamiento"),
]


class Command(BaseCommand):
    help = "Prepara tiendas, cuatro roles y productos de demostración"

    def handle(self, *args, **options):
        User = get_user_model()
        central, _ = Store.objects.get_or_create(name="Tienda Central", defaults={"location": "Lima"})
        norte, _ = Store.objects.get_or_create(name="Tienda Norte", defaults={"location": "Lima Norte"})
        password = os.environ.get("DEMO_PASSWORD") or ("D" + secrets.token_urlsafe(14) + "7!")
        people = [
            ("administrador", "admin@tecnostock.local", "Andrea Administradora", User.Role.ADMIN, None),
            ("gerente", "gerente@tecnostock.local", "Marco Gerente", User.Role.MANAGER, central),
            ("ventas", "ventas@tecnostock.local", "Valeria Ventas", User.Role.SALES, central),
            ("auditor", "auditor@tecnostock.local", "Alex Auditor", User.Role.AUDITOR, None),
        ]
        for username, email, full_name, role, store in people:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(username=username, email=email, password=password,
                                         full_name=full_name, role=role, store=store)
                self.stdout.write(f"Cuenta de ejemplo: {email}")
        for index, (code, name, category, price, stock, description) in enumerate(SAMPLES):
            Product.objects.get_or_create(code=code, defaults={
                "name": name, "store": central if index < 4 else norte,
                "category": category, "price": price, "stock": stock,
                "description": description,
            })
        self.stdout.write(self.style.SUCCESS("Datos de ejemplo listos. Contraseña inicial: " + password))
