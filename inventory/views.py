import os
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProductForm
from .models import Product


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "unhealthy"}, status=503)
    return JsonResponse({"status": "ok", "instance": os.environ.get("INSTANCE_NAME", "desarrollo")})


def instance(request):
    return JsonResponse({"instance": os.environ.get("INSTANCE_NAME", "desarrollo")})


@login_required
def product_list(request):
    search = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    products = Product.objects.all()
    if search:
        products = products.filter(Q(code__icontains=search) | Q(name__icontains=search))
    if category in Product.Category.values:
        products = products.filter(category=category)
    all_products = Product.objects.all()
    stats = {
        "products": all_products.count(),
        "units": all_products.aggregate(total=Sum("stock"))["total"] or 0,
        "low_stock": all_products.filter(stock__lt=10).count(),
        "categories": all_products.values("category").distinct().count(),
    }
    return render(request, "inventory/product_list.html", {
        "products": products, "search": search, "category": category,
        "categories": Product.Category.choices, "stats": stats,
    })


@login_required
def product_create(request):
    form = ProductForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Producto creado correctamente.")
        return redirect("inventory:list")
    return render(request, "inventory/product_form.html", {"form": form, "editing": False})


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Producto actualizado correctamente.")
        return redirect("inventory:list")
    return render(request, "inventory/product_form.html", {"form": form, "editing": True, "product": product})


@login_required
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, "Producto eliminado correctamente.")
    return redirect("inventory:list")
