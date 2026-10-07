from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.models import EmailAddress
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse
from .models import Store


class AppAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        # The public registration form enforces the laboratory's fields and policy.
        return False


class AppSocialAccountAdapter(DefaultSocialAccountAdapter):
    def can_authenticate_by_email(self, login, email):
        if login.account.provider != "google":
            return False
        if not EmailAddress.objects.filter(
            email__iexact=email, user__email__iexact=email,
            user__is_active=True, verified=True,
        ).exists():
            return False
        return super().can_authenticate_by_email(login, email)

    def get_connect_redirect_url(self, request, socialaccount):
        return reverse("profile")

    def is_open_for_signup(self, request, sociallogin):
        return True

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        user.full_name = user.get_full_name() or user.email.split("@")[0]
        user.role = user.Role.SALES
        user.store = Store.objects.order_by("id").first()
        user.save(update_fields=["full_name", "role", "store"])
        return user
