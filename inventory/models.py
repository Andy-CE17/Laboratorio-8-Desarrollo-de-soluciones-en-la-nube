from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    class Category(models.TextChoices):
        COMPUTERS = "computadoras", "Computadoras"
        MONITORS = "monitores", "Monitores"
        PERIPHERALS = "perifericos", "Periféricos"
        COMPONENTS = "componentes", "Componentes"
        OTHER = "otros", "Otros"

    code = models.CharField("código", max_length=20, unique=True)
    name = models.CharField("nombre", max_length=120)
    category = models.CharField("categoría", max_length=20, choices=Category.choices)
    description = models.TextField("descripción", blank=True)
    price = models.DecimalField("precio", max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.PositiveIntegerField("stock", default=0)
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} · {self.name}"

    @property
    def stock_status(self):
        if self.stock == 0:
            return "Agotado"
        if self.stock < 10:
            return "Stock bajo"
        return "Disponible"
