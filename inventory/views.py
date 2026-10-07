import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction
from django.db.models import Count, Q, Sum
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


def visible_products(user):
    products = Product.objects.select_related("store")
    if user.is_superuser or user.role in (user.Role.ADMIN, user.Role.AUDITOR):
        return products
    return products.filter(store=user.store) if user.store_id else products.none()


def forbidden(request):
    return render(request, "registration/forbidden.html", status=403)


@login_required
def product_list(request):
    search = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    all_products = visible_products(request.user)
    products = all_products
    if search:
        products = products.filter(Q(code__icontains=search) | Q(name__icontains=search))
    if category in Product.Category.values:
        products = products.filter(category=category)
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
    if not request.user.can_manage_products:
        return forbidden(request)
    form = ProductForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        if request.user.role == request.user.Role.MANAGER and not request.user.is_superuser:
            product.store = request.user.store
        product.save()
        messages.success(request, "Producto creado correctamente.")
        return redirect("inventory:list")
    return render(request, "inventory/product_form.html", {"form": form, "editing": False})


@login_required
def product_edit(request, pk):
    if not request.user.can_manage_products:
        return forbidden(request)
    product = get_object_or_404(Product, pk=pk)
    if request.user.role == request.user.Role.MANAGER and not request.user.is_superuser and product.store_id != request.user.store_id:
        return forbidden(request)
    form = ProductForm(request.POST or None, instance=product, user=request.user)
    if request.method == "POST" and form.is_valid():
        edited = form.save(commit=False)
        if request.user.role == request.user.Role.MANAGER and not request.user.is_superuser:
            edited.store = request.user.store
        edited.save()
        messages.success(request, "Producto actualizado correctamente.")
        return redirect("inventory:list")
    return render(request, "inventory/product_form.html", {"form": form, "editing": True, "product": product})


@login_required
@require_POST
def product_delete(request, pk):
    if not request.user.can_manage_products:
        return forbidden(request)
    product = get_object_or_404(Product, pk=pk)
    if request.user.role == request.user.Role.MANAGER and not request.user.is_superuser and product.store_id != request.user.store_id:
        return forbidden(request)
    product.delete()
    messages.success(request, "Producto eliminado correctamente.")
    return redirect("inventory:list")


@login_required
@require_POST
def stock_update(request, pk):
    if request.user.role not in (request.user.Role.ADMIN, request.user.Role.MANAGER, request.user.Role.SALES) and not request.user.is_superuser:
        return forbidden(request)
    try:
        stock = int(request.POST.get("stock", ""))
        if stock < 0:
            raise ValueError
    except ValueError:
        messages.error(request, "El stock debe ser un número entero no negativo.")
        return redirect("inventory:list")
    with transaction.atomic():
        product = get_object_or_404(visible_products(request.user).select_for_update(), pk=pk)
        product.stock = stock
        product.save(update_fields=["stock"])
    messages.success(request, f"Stock de {product.name} actualizado.")
    return redirect("inventory:list")


@login_required
def reports(request):
    if not request.user.can_view_reports:
        return forbidden(request)
    products = visible_products(request.user)
    by_store = products.values("store__name").annotate(products=Count("id"), units=Sum("stock")).order_by("store__name")
    return render(request, "inventory/reports.html", {
        "rows": by_store,
        "total_products": products.count(),
        "total_units": products.aggregate(total=Sum("stock"))["total"] or 0,
        "low_stock": products.filter(stock__lt=10).count(),
        "total_stores": products.exclude(store__isnull=True).values("store_id").distinct().count(),
    })
