"""Activate the language stored in the session for every request."""

from django.conf import settings
from django.utils import translation

SESSION_KEY = 'rgs_lang'


class LanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.session.get(SESSION_KEY) or settings.LANGUAGE_CODE
        if lang not in dict(settings.LANGUAGES):
            lang = settings.LANGUAGE_CODE
        translation.activate(lang)
        request.LANG = lang
        request.DIRECTION = 'rtl' if lang == 'ar' else 'ltr'
        response = self.get_response(request)
        response.setdefault('Content-Language', lang)
        return response
