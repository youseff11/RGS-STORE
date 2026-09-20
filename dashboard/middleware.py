"""Activate the visitor's language (Arabic by default) for every request.

Order of precedence: ?lang=xx in the URL (handy for shared links) → the
`rgs_lang` cookie set by the navbar button → Arabic.
The dashboard is always Arabic.
"""

from django.utils import translation

from .i18n import DEFAULT_LANG, LANGS

COOKIE = 'rgs_lang'
COOKIE_AGE = 60 * 60 * 24 * 365


class LanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from_query = (request.GET.get('lang') or '').lower()
        if request.path.startswith('/dashboard') or request.path.startswith('/django-admin'):
            lang = 'ar'
        elif from_query in LANGS:
            lang = from_query
        else:
            lang = request.COOKIES.get(COOKIE) or DEFAULT_LANG
            if lang not in LANGS:
                lang = DEFAULT_LANG

        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        response.headers.setdefault('Content-Language', lang)
        if from_query in LANGS and request.COOKIES.get(COOKIE) != from_query:
            response.set_cookie(COOKIE, from_query, max_age=COOKIE_AGE, samesite='Lax')
        translation.deactivate()
        return response
