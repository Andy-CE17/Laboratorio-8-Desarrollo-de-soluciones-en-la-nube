from django.shortcuts import redirect


class MFAGateMiddleware:
    EXEMPT = ("/mfa/", "/login/", "/logout/", "/register/", "/accounts/", "/static/", "/health/", "/instance/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in ("/accounts/login/", "/accounts/signup/"):
            return redirect("login" if request.path.endswith("login/") else "register")
        if (request.user.is_authenticated
                and not request.path.startswith(self.EXEMPT)
                and request.session.get("mfa_verified_user_id") != request.user.pk):
            return redirect("mfa")
        return self.get_response(request)
