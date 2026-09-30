import os
import secrets
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from inventory.models import Product


SAMPLES = [
    ("TEC-001", "Laptop Pro 14", "computadoras", Decimal("3299.00"), 18, "Equipo portátil de 14 pulgadas"),
    ("TEC-002", "Monitor Ultra 27", "monitores", Decimal("1099.00"), 7, "Monitor de alta resolución"),
    ("TEC-003", "Teclado Mecánico", "perifericos", Decimal("279.00"), 32, "Teclado compacto"),
    ("TEC-004", "Mouse Inalámbrico", "perifericos", Decimal("129.00"), 42, "Mouse ergonómico"),
    ("TEC-005", "SSD NVMe 1 TB", "componentes", Decimal("379.00"), 9, "Unidad de almacenamiento"),
]


class Command(BaseCommand):
    help = "Crea un usuario de demostración y productos de ejemplo"

    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(username="laboratorio")
        if created:
            password = os.environ.get("DEMO_PASSWORD") or secrets.token_urlsafe(14)
            user.set_password(password)
            user.save(update_fields=["password"])
            self.stdout.write(f"Usuario: laboratorio | Contraseña inicial: {password}")
        else:
            self.stdout.write("El usuario laboratorio ya existe; su contraseña no cambió.")
        for code, name, category, price, stock, description in SAMPLES:
            Product.objects.get_or_create(code=code, defaults={
                "name": name, "category": category, "price": price,
                "stock": stock, "description": description,
            })
        self.stdout.write(self.style.SUCCESS("Datos de demostración preparados."))
