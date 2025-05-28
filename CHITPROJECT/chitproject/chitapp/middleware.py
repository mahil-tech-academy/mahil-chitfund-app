from django.shortcuts import redirect
from django.conf import settings
from django.urls import resolve

EXEMPT_URLS = [settings.LOGIN_URL]

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        if not request.user.is_authenticated:
            if path not in EXEMPT_URLS:
                return redirect(settings.LOGIN_URL)
        return self.get_response(request)
