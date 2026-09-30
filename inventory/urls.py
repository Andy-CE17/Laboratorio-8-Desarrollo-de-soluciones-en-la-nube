from django.urls import path
from . import views

app_name = "inventory"
urlpatterns = [
    path("", views.product_list, name="list"),
    path("products/new/", views.product_create, name="create"),
    path("products/<int:pk>/edit/", views.product_edit, name="edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="delete"),
    path("health/", views.health, name="health"),
    path("instance/", views.instance, name="instance"),
]
