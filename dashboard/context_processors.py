"""Data every template on the site needs."""

from .i18n import current_lang
from .models import Announcement, Category, SiteSettings
from .utils import Cart


def store(request):
    lang = current_lang()
    try:
        settings_obj = SiteSettings.load()
    except Exception:  # database not migrated yet
        settings_obj = None

    path = request.path or ''
    is_dashboard = path.startswith('/dashboard')

    data = {
        'SITE': settings_obj,
        'LANG': lang,
        'DIR': 'ltr',
        'IS_RTL': False,
        'CURRENCY': settings_obj.currency if settings_obj else '',
    }

    if not is_dashboard and settings_obj is not None:
        cart = Cart(request)
        data.update({
            'NAV_CATEGORIES': Category.objects.filter(is_active=True),
            'ANNOUNCEMENTS': Announcement.objects.filter(is_active=True),
            'CART': cart,
            'CART_COUNT': cart.count,
        })
    return data
