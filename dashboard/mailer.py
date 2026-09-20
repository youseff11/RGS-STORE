"""Email notifications — RGS TOWER.

Everything is driven by «الإشعارات والإيميل» in the dashboard (`SiteSettings`):
the Gmail (or any SMTP) account that sends, the address that receives, and a
switch per event. Nothing here ever raises: a store that cannot send email must
still take orders, so every failure is swallowed and reported in the log only.

Each mail is sent on a background thread so the shopper never waits for Gmail.
"""

import logging
import threading

from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import SiteSettings

log = logging.getLogger(__name__)

TIMEOUT = 15  # seconds — never hang on a slow SMTP server


def _connection(site):
    """The SMTP account saved in the dashboard.

    Built directly (with its own `alias`) so Django reads the host, the user and
    the app password from the dashboard and not from the project's MAILERS
    setting — that one stays the console backend for development.
    """
    use_ssl = not site.smtp_use_tls and int(site.smtp_port or 0) == 465
    options = dict(
        host=site.smtp_host, port=int(site.smtp_port or 587),
        username=site.smtp_user, password=site.smtp_password,
        use_tls=bool(site.smtp_use_tls) and not use_ssl, use_ssl=use_ssl,
        timeout=TIMEOUT,
    )
    try:
        return EmailBackend(alias='rgs-dashboard', **options)
    except TypeError:  # older Django: no per-connection alias
        return EmailBackend(**options)


def send_now(site, to, subject, template, context):
    """Render + send one mail. Returns (ok, error message)."""
    recipients = [address for address in (to if isinstance(to, (list, tuple)) else [to]) if address]
    if not recipients:
        return False, 'مفيش إيميل مستقبِل'
    body_html = render_to_string(template, {**context, 'site': site, 'subject': subject})
    message = EmailMultiAlternatives(
        subject=subject,
        body=strip_tags(body_html.replace('</p>', '</p>\n').replace('<br>', '\n')),
        from_email=site.mail_from or site.smtp_user,
        to=recipients,
        connection=_connection(site),
    )
    message.attach_alternative(body_html, 'text/html')
    message.send()
    return True, ''


def _send_async(to, subject, template, context):
    site = SiteSettings.load()
    if not site.mail_ready:
        return

    def run():
        try:
            send_now(site, to, subject, template, context)
        except Exception as error:  # noqa: BLE001 — email must never break a request
            log.warning('RGS mail failed (%s): %s', subject, error)

    threading.Thread(target=run, daemon=True).start()


def _owner(site):
    return site.notify_email or site.smtp_user


# ---------------------------------------------------------------- the events
def order_placed(order):
    """New order: the owner gets the details, the customer gets a confirmation."""
    site = SiteSettings.load()
    if not site.mail_ready:
        return
    brand = site.brand_name_ar or site.brand_name_en
    if site.notify_new_order and _owner(site):
        _send_async(
            _owner(site), f'طلب جديد {order.order_number} — {order.full_name}',
            'emails/order_admin.html',
            {'order': order, 'url': site.absolute_url(f'/dashboard/orders/{order.pk}/')},
        )
    if site.notify_customer_order and order.email:
        _send_async(
            order.email, f'تأكيد طلبك {order.order_number} — {brand}',
            'emails/order_customer.html',
            {'order': order, 'url': site.absolute_url(f'/order/{order.order_number}/success/')},
        )


def ticket_opened(ticket, message):
    site = SiteSettings.load()
    if not (site.mail_ready and site.notify_new_ticket and _owner(site)):
        return
    _send_async(
        _owner(site), f'تذكرة جديدة {ticket.number} — {ticket.subject}',
        'emails/ticket_admin.html',
        {'ticket': ticket, 'message': message, 'is_reply': False,
         'url': site.absolute_url(f'/dashboard/tickets/{ticket.pk}/')},
    )


def ticket_customer_replied(ticket, message):
    site = SiteSettings.load()
    if not (site.mail_ready and site.notify_new_ticket and _owner(site)):
        return
    _send_async(
        _owner(site), f'رد جديد على التذكرة {ticket.number} — {ticket.subject}',
        'emails/ticket_admin.html',
        {'ticket': ticket, 'message': message, 'is_reply': True,
         'url': site.absolute_url(f'/dashboard/tickets/{ticket.pk}/')},
    )


def ticket_staff_replied(ticket, message):
    site = SiteSettings.load()
    if not (site.mail_ready and site.notify_customer_ticket):
        return
    email = ticket.user.email
    if not email:
        return
    brand = site.brand_name_ar or site.brand_name_en
    _send_async(
        email, f'رد على تذكرتك {ticket.number} — {brand}',
        'emails/ticket_customer.html',
        {'ticket': ticket, 'message': message,
         'url': site.absolute_url(f'/support/{ticket.number}/')},
    )


def contact_message(contact):
    site = SiteSettings.load()
    if not (site.mail_ready and site.notify_new_message and _owner(site)):
        return
    _send_async(
        _owner(site), f'رسالة جديدة من {contact.name}',
        'emails/message_admin.html',
        {'contact': contact, 'url': site.absolute_url(f'/dashboard/messages/{contact.pk}/')},
    )


def review_added(review):
    site = SiteSettings.load()
    if not (site.mail_ready and site.notify_new_review and _owner(site)):
        return
    _send_async(
        _owner(site), f'تقييم جديد {review.rating}/5 من {review.name}',
        'emails/review_admin.html',
        {'review': review, 'url': site.absolute_url('/dashboard/reviews/')},
    )


def send_test(site, to):
    """Used by the «جرّب الإرسال» button — this one reports its error."""
    try:
        return send_now(site, to, f'تجربة إيميل — {site.brand_name_ar or site.brand_name_en}',
                        'emails/test.html', {})
    except Exception as error:  # noqa: BLE001 — the dashboard shows the reason
        return False, str(error)
