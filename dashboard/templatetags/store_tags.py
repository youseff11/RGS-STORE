"""Template helpers: bilingual strings, money formatting, querystring building."""

from decimal import Decimal, InvalidOperation

from django import template
from django.http import QueryDict
from django.utils.html import escape
from django.utils.safestring import mark_safe

from ..i18n import current_lang, t as translate
from ..models import SiteSettings

register = template.Library()


@register.simple_tag
def t(key, **kwargs):
    """{% t "add_to_cart" %} — bilingual UI string."""
    return translate(key, **kwargs)


@register.simple_tag
def lang():
    return current_lang()


@register.filter
def loc(obj, field):
    """{{ product|loc:"name" }} — pick <field>_ar / <field>_en by language."""
    if obj is None:
        return ''
    suffix = 'ar' if current_lang() == 'ar' else 'en'
    other = 'en' if suffix == 'ar' else 'ar'
    value = getattr(obj, f'{field}_{suffix}', None)
    if not value:
        value = getattr(obj, f'{field}_{other}', None)
    if not value:
        value = getattr(obj, field, '')
    return value or ''


@register.filter
def money(value):
    """1234.5 -> 1,234.50 (decimals dropped when they are .00)"""
    try:
        amount = Decimal(value or 0)
    except (TypeError, ValueError, InvalidOperation):
        return value
    quantized = amount.quantize(Decimal('0.01'))
    if quantized == quantized.to_integral_value():
        return f'{int(quantized):,}'
    return f'{quantized:,.2f}'


@register.simple_tag(takes_context=True)
def price(context, value):
    """Amount + currency, ready to print."""
    currency = context.get('CURRENCY')
    if currency is None:
        try:
            currency = SiteSettings.load().currency
        except Exception:
            currency = ''
    return mark_safe(f'{money(value)} <span class="cur">{escape(currency)}</span>')


@register.simple_tag(takes_context=True)
def qs(context, **kwargs):
    """Rebuild the current querystring with overrides: {% qs page=2 %}"""
    request = context.get('request')
    params = request.GET.copy() if request else QueryDict('', mutable=True)
    for key, value in kwargs.items():
        if value in (None, '', 'None'):
            params.pop(key, None)
        else:
            params[key] = value
    if 'page' not in kwargs:
        params.pop('page', None)
    encoded = params.urlencode()
    return f'?{encoded}' if encoded else '?'


@register.filter
def get_item(dictionary, key):
    try:
        return dictionary.get(key)
    except AttributeError:
        return None


@register.filter
def field_class(field, css):
    return field.as_widget(attrs={'class': css})


@register.filter
def sub(value, arg):
    try:
        return Decimal(value or 0) - Decimal(arg or 0)
    except (TypeError, ValueError, InvalidOperation):
        return 0


@register.filter
def mul(value, arg):
    try:
        return Decimal(value or 0) * Decimal(arg or 0)
    except (TypeError, ValueError, InvalidOperation):
        return 0


@register.simple_tag
def status_color(status):
    return {
        'pending': 'warn',
        'confirmed': 'info',
        'shipped': 'accent',
        'delivered': 'ok',
        'cancelled': 'bad',
    }.get(status, 'muted')
