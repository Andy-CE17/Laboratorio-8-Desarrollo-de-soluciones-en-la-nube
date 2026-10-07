from django.contrib import admin
from django.urls import include, path
from accounts import views as account_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", account_views.login_view, name="login"),
    path("logout/", account_views.logout_view, name="logout"),
    path("register/", account_views.register_view, name="register"),
    path("mfa/", account_views.mfa_view, name="mfa"),
    path("api/session/", account_views.session_api, name="session-api"),
    path("profile/", account_views.profile_view, name="profile"),
    path("team/", account_views.team_view, name="team"),
    path("team/<int:pk>/", account_views.team_edit_view, name="team-edit"),
    path("stores/", account_views.stores_view, name="stores"),
    path("stores/<int:pk>/", account_views.store_edit_view, name="store-edit"),
    path("accounts/", include("allauth.urls")),
    path("", include("inventory.urls")),
]
