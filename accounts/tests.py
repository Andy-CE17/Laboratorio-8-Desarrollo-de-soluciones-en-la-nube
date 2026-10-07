import pyotp
from allauth.core.context import request_context
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .models import Store
from .adapters import AppSocialAccountAdapter


class AuthenticationTests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="Central")
        self.user = get_user_model().objects.create_user(
            username="demo", email="demo@test.local", password="Test2026!",
            full_name="Usuario Demo", store=self.store,
        )

    def test_registration_password_policy_and_email_uniqueness(self):
        login_page = self.client.get(reverse("login"))
        self.assertContains(login_page, 'id="register-panel"')
        self.assertContains(login_page, 'data-auth-open="register"')
        self.assertContains(self.client.get(reverse("register")), 'id="register-panel"')
        data = {"full_name": "Nueva Persona", "email": "new@test.local",
                "store": self.store.pk, "password1": "simple", "password2": "simple"}
        self.assertContains(self.client.post(reverse("register"), data), "mayúscula")
        data["password1"] = data["password2"] = "Seguro2026!"
        self.assertRedirects(self.client.post(reverse("register"), data), reverse("mfa"))
        self.assertTrue(get_user_model().objects.filter(email="new@test.local").exists())
        self.client.post(reverse("logout"))
        self.assertContains(self.client.post(reverse("register"), data), "Ya existe una cuenta")

    def test_localhost_entry_uses_google_authorized_origin(self):
        self.assertRedirects(
            self.client.get(reverse("login"), HTTP_HOST="localhost:8001"),
            "http://127.0.0.1:8001/login/", fetch_redirect_response=False,
        )
        self.assertRedirects(
            self.client.get(reverse("register"), HTTP_HOST="localhost:8001"),
            "http://127.0.0.1:8001/register/", fetch_redirect_response=False,
        )

    def test_five_failures_lock_account(self):
        for _ in range(5):
            self.client.post(reverse("login"), {"email": self.user.email, "password": "incorrect"})
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.locked_until)
        self.assertContains(self.client.post(reverse("login"), {"email": self.user.email, "password": "Test2026!"}), "bloqueado")

    def test_totp_then_jwt_and_three_attempt_limit(self):
        self.assertRedirects(self.client.post(reverse("login"), {"email": self.user.email, "password": "Test2026!"}), reverse("mfa"))
        secret = self.client.session["pending_totp_secret"] if "pending_totp_secret" in self.client.session else None
        if not secret:
            self.client.get(reverse("mfa"))
            secret = self.client.session["pending_totp_secret"]
        response = self.client.post(reverse("mfa"), {"code": pyotp.TOTP(secret).now()})
        self.assertRedirects(response, reverse("inventory:list"))
        self.assertIn("techstore_access", response.cookies)
        self.assertEqual(self.client.get(reverse("session-api")).json()["role"], "sales")
        self.client.post(reverse("logout"))
        self.client.post(reverse("login"), {"email": self.user.email, "password": "Test2026!"})
        for _ in range(2):
            self.assertEqual(self.client.post(reverse("mfa"), {"code": "000000"}).status_code, 200)
        self.assertRedirects(self.client.post(reverse("mfa"), {"code": "000000"}), reverse("login"))

    def test_each_user_can_update_own_photo_and_admin_can_see_it(self):
        User = get_user_model()
        other = User.objects.create_user(
            username="other", email="other@test.local", password="Test2026!",
            full_name="Otra Persona", role=User.Role.ADMIN,
        )
        self.client.force_login(self.user)
        session = self.client.session
        session["mfa_verified_user_id"] = self.user.pk
        session.save()
        photo = "https://images.example.test/profile.png"
        self.assertRedirects(self.client.post(reverse("profile"), {"avatar_url": photo}), reverse("profile"))
        self.user.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(self.user.avatar_url, photo)
        self.assertEqual(other.avatar_url, "")
        self.assertContains(self.client.get(reverse("inventory:list")), photo)
        self.assertContains(self.client.post(reverse("profile"), {"avatar_url": "http://example.test/photo.jpg"}), "HTTPS")
        self.user.refresh_from_db()
        self.assertEqual(self.user.avatar_url, photo)

        self.client.force_login(other)
        session = self.client.session
        session["mfa_verified_user_id"] = other.pk
        session.save()
        self.assertContains(self.client.get(reverse("team")), photo)

    def test_verified_google_email_uses_existing_verified_account(self):
        request = RequestFactory().get("/accounts/google/login/callback/")
        adapter = AppSocialAccountAdapter(request)
        google = adapter.get_provider(request, "google")
        address = EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True, primary=True,
        )
        sociallogin = SocialLogin(
            account=SocialAccount(provider="google", uid="new-google-user"),
            provider=google,
            email_addresses=[EmailAddress(email=self.user.email, verified=True)],
        )
        self.assertEqual(adapter.authenticate_by_email(sociallogin)[0], self.user)
        with request_context(request):
            sociallogin.lookup()
            self.assertEqual(sociallogin.user, self.user)
            sociallogin._accept_login(request)
        self.assertTrue(SocialAccount.objects.filter(
            user=self.user, provider="google", uid="new-google-user",
        ).exists())
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Test2026!"))
        address.verified = False
        address.save(update_fields=["verified"])
        self.assertIsNone(adapter.authenticate_by_email(sociallogin))
