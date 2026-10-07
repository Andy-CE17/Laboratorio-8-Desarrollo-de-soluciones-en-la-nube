import base64
import io
import uuid
from datetime import datetime, timedelta, timezone as dt_timezone

import jwt
import pyotp
import qrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from allauth.socialaccount.models import SocialAccount

from .forms import ProfilePhotoForm, RegistrationForm, StoreForm, TeamEditForm
from .models import Store

User = get_user_model()
LOCK_MINUTES = 15
JWT_MINUTES = 15


def _safe_next(request):
    candidate = request.POST.get("next") or request.GET.get("next") or reverse("inventory:list")
    if url_has_allowed_host_and_scheme(candidate, {request.get_host()}, require_https=request.is_secure()):
        return candidate
    return reverse("inventory:list")


def _auth_page_context(request, **overrides):
    context = {
        "error": "",
        "next": _safe_next(request),
        "registration_form": RegistrationForm(auto_id="id_register_%s"),
        "show_register": False,
        "google_ready": bool(settings.SOCIALACCOUNT_PROVIDERS["google"].get("APP")),
        "github_ready": bool(settings.SOCIALACCOUNT_PROVIDERS["github"].get("APP")),
    }
    context.update(overrides)
    return context


def _canonical_local_entry(request):
    if request.method == "GET" and request.get_host().lower() == "localhost:8001":
        return HttpResponseRedirect("http://127.0.0.1:8001" + request.get_full_path())
    return None


def _issue_token(response, user, request):
    now = datetime.now(dt_timezone.utc)
    token = jwt.encode({
        "sub": str(user.pk), "iat": now, "exp": now + timedelta(minutes=JWT_MINUTES),
        "jti": uuid.uuid4().hex,
    }, settings.SECRET_KEY, algorithm="HS256")
    response.set_cookie(
        "techstore_access", token, max_age=JWT_MINUTES * 60,
        httponly=True, secure=request.is_secure(), samesite="Lax",
    )
    return response


def login_view(request):
    canonical = _canonical_local_entry(request)
    if canonical:
        return canonical
    if request.user.is_authenticated:
        return redirect("inventory:list")
    error = ""
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        with transaction.atomic():
            user = User.objects.select_for_update().filter(email__iexact=email).first()
            if user and user.locked_until and user.locked_until > timezone.now():
                error = "Acceso temporalmente bloqueado. Inténtalo más tarde."
            elif user:
                authenticated = authenticate(request, username=user.username, password=password)
                if authenticated and authenticated.is_active:
                    user.failed_login_attempts = 0
                    user.locked_until = None
                    user.save(update_fields=["failed_login_attempts", "locked_until"])
                    login(request, authenticated)
                    request.session["post_mfa_next"] = _safe_next(request)
                    return redirect("mfa")
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = timezone.now() + timedelta(minutes=LOCK_MINUTES)
                user.save(update_fields=["failed_login_attempts", "locked_until"])
                error = "Credenciales incorrectas o acceso no disponible."
            else:
                error = "Credenciales incorrectas o acceso no disponible."
    return render(request, "registration/login.html", _auth_page_context(request, error=error))


@require_POST
def logout_view(request):
    logout(request)
    response = redirect("login")
    response.delete_cookie("techstore_access")
    return response


def register_view(request):
    canonical = _canonical_local_entry(request)
    if canonical:
        return canonical
    if request.user.is_authenticated:
        return redirect("inventory:list")
    form = RegistrationForm(request.POST or None, auto_id="id_register_%s")
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = User.objects.create_user(
                username="user-" + uuid.uuid4().hex[:12],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password1"],
                full_name=form.cleaned_data["full_name"].strip(),
                store=form.cleaned_data["store"],
                role=User.Role.SALES,
            )
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.info(request, "Cuenta creada. Configura tu segundo factor para continuar.")
        return redirect("mfa")
    return render(request, "registration/login.html", _auth_page_context(
        request, registration_form=form, show_register=True,
    ))


@login_required
def mfa_view(request):
    user = request.user
    if request.session.get("mfa_verified_user_id") == user.pk:
        return redirect("inventory:list")
    enrolling = not bool(user.totp_secret)
    secret = user.totp_secret
    if enrolling:
        secret = request.session.get("pending_totp_secret")
        if not secret:
            secret = pyotp.random_base32()
            request.session["pending_totp_secret"] = secret
    error = ""
    if request.method == "POST":
        code = request.POST.get("code", "").replace(" ", "").strip()
        if code.isdigit() and len(code) == 6 and pyotp.TOTP(secret).verify(code, valid_window=1):
            if enrolling:
                user.totp_secret = secret
                user.save(update_fields=["totp_secret"])
                request.session.pop("pending_totp_secret", None)
            request.session["mfa_verified_user_id"] = user.pk
            request.session.pop("mfa_attempts", None)
            destination = request.session.pop("post_mfa_next", reverse("inventory:list"))
            if not url_has_allowed_host_and_scheme(destination, {request.get_host()}, require_https=request.is_secure()):
                destination = reverse("inventory:list")
            return _issue_token(redirect(destination), user, request)
        attempts = request.session.get("mfa_attempts", 0) + 1
        request.session["mfa_attempts"] = attempts
        if attempts >= 3:
            logout(request)
            messages.error(request, "Se agotaron los tres intentos de verificación.")
            return redirect("login")
        error = f"Código incorrecto. Te quedan {3 - attempts} intentos."
    qr = ""
    if enrolling:
        uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="TechStore")
        img = qrcode.make(uri)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr = base64.b64encode(buffer.getvalue()).decode("ascii")
    return render(request, "registration/mfa.html", {
        "enrolling": enrolling, "secret": secret if enrolling else "",
        "qr": qr, "error": error,
    })


def session_api(request):
    token = request.COOKIES.get("techstore_access", "")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
        return JsonResponse({"detail": "Token ausente o inválido"}, status=401)
    if (not request.user.is_authenticated
            or request.session.get("mfa_verified_user_id") != request.user.pk
            or payload.get("sub") != str(request.user.pk)):
        return JsonResponse({"detail": "Sesión no verificada"}, status=401)
    return JsonResponse({
        "user": request.user.email, "role": request.user.role,
        "store": request.user.store.name if request.user.store else None,
    })


@login_required
def profile_view(request):
    form = ProfilePhotoForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Foto de perfil actualizada.")
        return redirect("profile")
    return render(request, "accounts/profile.html", {
        "form": form,
        "connected_providers": set(SocialAccount.objects.filter(user=request.user).values_list("provider", flat=True)),
        "google_ready": bool(settings.SOCIALACCOUNT_PROVIDERS["google"].get("APP")),
        "github_ready": bool(settings.SOCIALACCOUNT_PROVIDERS["github"].get("APP")),
    })


@login_required
def team_view(request):
    if not request.user.can_manage_users:
        return render(request, "registration/forbidden.html", status=403)
    search = request.GET.get("q", "").strip()
    members = User.objects.select_related("store").order_by("full_name")
    if search:
        members = members.filter(
            Q(full_name__icontains=search) | Q(email__icontains=search)
            | Q(username__icontains=search)
        )
    return render(request, "accounts/team.html", {
        "members": members, "search": search,
        "total_members": User.objects.count(),
        "active_members": User.objects.filter(is_active=True).count(),
    })


@login_required
def team_edit_view(request, pk):
    if not request.user.can_manage_users:
        return render(request, "registration/forbidden.html", status=403)
    member = get_object_or_404(User, pk=pk)
    form = TeamEditForm(request.POST or None, instance=member)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Permisos del usuario actualizados.")
        return redirect("team")
    return render(request, "accounts/team_edit.html", {"form": form, "member": member})


@login_required
def stores_view(request):
    if not request.user.can_manage_users:
        return render(request, "registration/forbidden.html", status=403)
    form = StoreForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Tienda creada correctamente.")
        return redirect("stores")
    return render(request, "accounts/stores.html", {
        "form": form, "stores": Store.objects.annotate(product_count=Count("products")),
    })


@login_required
def store_edit_view(request, pk):
    if not request.user.can_manage_users:
        return render(request, "registration/forbidden.html", status=403)
    store = get_object_or_404(Store, pk=pk)
    form = StoreForm(request.POST or None, instance=store)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Configuración de tienda actualizada.")
        return redirect("stores")
    return render(request, "accounts/store_edit.html", {"form": form, "store": store})
