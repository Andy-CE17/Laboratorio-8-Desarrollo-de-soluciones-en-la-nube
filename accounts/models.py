from django.contrib.auth.models import AbstractUser
from django.core.validators import URLValidator
from django.db import models


class Store(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrador"
        MANAGER = "manager", "Gerente de tienda"
        SALES = "sales", "Empleado de ventas"
        AUDITOR = "auditor", "Auditor"

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    avatar_url = models.URLField(max_length=500, blank=True, validators=[URLValidator(schemes=["https"])])
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.SALES)
    store = models.ForeignKey(Store, null=True, blank=True, on_delete=models.SET_NULL, related_name="users")
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    totp_secret = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return self.full_name or self.email or self.username

    @property
    def can_manage_products(self):
        return self.is_superuser or self.role in (self.Role.ADMIN, self.Role.MANAGER)

    @property
    def can_manage_users(self):
        return self.is_superuser or self.role == self.Role.ADMIN

    @property
    def can_view_reports(self):
        return self.is_superuser or self.role in (self.Role.ADMIN, self.Role.MANAGER, self.Role.AUDITOR)
