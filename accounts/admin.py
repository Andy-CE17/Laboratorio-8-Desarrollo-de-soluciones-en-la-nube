from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Store, User


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "location")


@admin.register(User)
class TechStoreUserAdmin(UserAdmin):
    list_display = ("photo_preview", "username", "email", "full_name", "role", "store", "is_active")
    readonly_fields = ("photo_preview",)
    fieldsets = UserAdmin.fieldsets + (
        ("TechStore", {"fields": ("full_name", "avatar_url", "photo_preview", "role", "store", "failed_login_attempts", "locked_until", "totp_secret")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("TechStore", {"fields": ("email", "full_name", "avatar_url", "role", "store")}),
    )

    @admin.display(description="Foto")
    def photo_preview(self, obj):
        if not obj or not obj.avatar_url:
            return "—"
        return format_html(
            '<img src="{}" width="40" height="40" alt="Foto de {}" referrerpolicy="no-referrer" '
            'style="object-fit:cover;border-radius:50%;">',
            obj.avatar_url, obj.full_name or obj.username,
        )
