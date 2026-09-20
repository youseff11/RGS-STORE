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


@register.simple_tag
def payment_color(status):
    return {
        'unpaid': 'muted',
        'pending': 'warn',
        'paid': 'ok',
        'failed': 'bad',
        'refunded': 'info',
    }.get(status, 'muted')


@register.filter
def form_rows(form):
    """Group `<x>_ar` + `<x>_en` fields into one row so they render side by side."""
    rows = []
    fields = list(form)
    i = 0
    while i < len(fields):
        field = fields[i]
        name = field.name
        if name.endswith('_ar') and i + 1 < len(fields) and fields[i + 1].name == name[:-3] + '_en':
            rows.append([field, fields[i + 1]])
            i += 2
            continue
        rows.append([field])
        i += 1
    return rows


@register.filter
def field_lang(bound_field):
    return getattr(bound_field.field, 'lang', '')


@register.filter
def is_checkbox(bound_field):
    from django.forms import CheckboxInput
    return isinstance(bound_field.field.widget, CheckboxInput)


@register.simple_tag(takes_context=True)
def absolute(context, url):
    """Absolute URL for Open Graph tags (WhatsApp / Facebook need the full address)."""
    request = context.get('request')
    if not url:
        return ''
    if url.startswith('http://') or url.startswith('https://'):
        return url
    return request.build_absolute_uri(url) if request else url


@register.simple_tag(takes_context=True)
def lang_switch_url(context, code):
    request = context.get('request')
    from django.urls import reverse
    base = reverse('set_language', args=[code])
    if request is None:
        return base
    return f'{base}?next={_quote(request.get_full_path())}'


def _quote(value):
    from urllib.parse import quote
    return quote(value, safe='/')


@register.filter
def rich_text(value):
    """Plain text from the dashboard → paragraphs; lines starting with # become headings,
    lines starting with - or • become bullet points."""
    if not value:
        return ''
    html, bullets, para = [], [], []

    def flush_para():
        if para:
            html.append('<p>' + '<br>'.join(escape(line) for line in para) + '</p>')
            para.clear()

    def flush_bullets():
        if bullets:
            html.append('<ul>' + ''.join(f'<li>{escape(b)}</li>' for b in bullets) + '</ul>')
            bullets.clear()

    for raw in str(value).replace('\r\n', '\n').split('\n'):
        line = raw.strip()
        if not line:
            flush_para()
            flush_bullets()
            continue
        if line.startswith('#'):
            flush_para()
            flush_bullets()
            level = 'h3' if line.startswith('##') else 'h2'
            html.append(f'<{level}>{escape(line.lstrip("#").strip())}</{level}>')
        elif line[:1] in ('-', '•', '*') and len(line) > 1:
            flush_para()
            bullets.append(line[1:].strip())
        else:
            flush_bullets()
            para.append(line)
    flush_para()
    flush_bullets()
    return mark_safe(''.join(html))


@register.filter
def star_range(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = 0
    return range(max(0, min(5, value)))


@register.filter
def empty_star_range(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = 0
    return range(5 - max(0, min(5, value)))
