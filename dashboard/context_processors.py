"""Data every template on the site needs."""

from .i18n import current_lang
from .models import (
    Announcement, Category, NavLink, Policy, SiteSettings, Ticket, staff_permissions,
)
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
        'ALT_LANG': 'en' if lang == 'ar' else 'ar',
        'DIR': 'rtl' if lang == 'ar' else 'ltr',
        'IS_RTL': lang == 'ar',
        'CURRENCY': settings_obj.currency if settings_obj else '',
    }

    if is_dashboard:
        data['DASH_PERMS'] = staff_permissions(getattr(request, 'user', None))
        return data

    if settings_obj is not None:
        cart = Cart(request)
        nav_links = [
            link for link in NavLink.objects.select_related('category', 'policy')
            if link.is_visible
        ]
        user = getattr(request, 'user', None)
        data.update({
            'NAV_LINKS': nav_links,
            'NAV_CATEGORIES': Category.objects.filter(is_active=True),
            'FOOTER_POLICIES': [
                p for p in Policy.objects.filter(is_active=True, show_in_footer=True) if p.has_content
            ],
            'ANNOUNCEMENTS': Announcement.objects.filter(is_active=True),
            'CART': cart,
            'CART_COUNT': cart.count,
            'IS_CUSTOMER': bool(user and user.is_authenticated and not user.is_staff),
        })
        # tickets badge: the store's staff see what customers sent, a customer
        # sees the replies waiting for them
        support_staff = bool(
            user is not None and user.is_authenticated
            and 'messages' in staff_permissions(user)
        )
        if support_staff:
            unread = Ticket.objects.filter(admin_unread=True).exclude(status='closed').count()
        elif user is not None and user.is_authenticated:
            unread = Ticket.objects.filter(user=user, user_unread=True).count()
        else:
            unread = 0
        data['SUPPORT_STAFF'] = support_staff
        data['TICKETS_UNREAD'] = unread
    return data
