from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "price", "stock", "updated_at")
    search_fields = ("code", "name")
    list_filter = ("category",)
