"""Minimal PayPal REST client (Orders v2) — standard library only.

Used by the official PayPal button: the browser asks our server to create the
PayPal order, the customer approves it in the PayPal popup, then our server
captures it and checks the amount before the order is marked as paid.
"""

import base64
import json
import urllib.error
import urllib.request
from decimal import Decimal

from django.core.cache import cache

LIVE = 'https://api-m.paypal.com'
SANDBOX = 'https://api-m.sandbox.paypal.com'
TIMEOUT = 20


class PayPalError(Exception):
    def __init__(self, message, status=None, payload=None):
        super().__init__(message)
        self.status = status
        self.payload = payload or {}


def _base(site):
    return SANDBOX if site.paypal_sandbox else LIVE


def _request(url, *, method='GET', headers=None, data=None):
    body = None
    if data is not None:
        body = data if isinstance(data, bytes) else json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode('utf-8') or '{}'
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode('utf-8') or '{}')
        except ValueError:
            payload = {}
        raise PayPalError(payload.get('message') or str(exc), exc.code, payload) from exc
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise PayPalError(str(exc)) from exc


def access_token(site):
    key = f'paypal-token:{site.paypal_sandbox}:{site.paypal_client_id[-8:]}'
    token = cache.get(key)
    if token:
        return token
    auth = base64.b64encode(f'{site.paypal_client_id}:{site.paypal_secret}'.encode()).decode()
    data = _request(
        _base(site) + '/v1/oauth2/token', method='POST',
        headers={
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
        },
        data=b'grant_type=client_credentials',
    )
    token = data.get('access_token')
    if not token:
        raise PayPalError('No access token returned')
    cache.set(key, token, max(60, int(data.get('expires_in', 3000)) - 120))
    return token


def _api(site, path, *, method='GET', data=None, request_id=None):
    headers = {
        'Authorization': f'Bearer {access_token(site)}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    if request_id:
        headers['PayPal-Request-Id'] = request_id
    return _request(_base(site) + path, method=method, headers=headers, data=data)


def create_order(site, order, brand_name=''):
    payload = {
        'intent': 'CAPTURE',
        'purchase_units': [{
            'reference_id': order.order_number,
            'custom_id': order.order_number,
            'invoice_id': order.order_number,
            'description': f'{brand_name} — {order.order_number}'.strip(' —')[:127],
            'amount': {
                'currency_code': order.pay_currency or site.paypal_currency or 'USD',
                'value': f'{order.pay_amount:.2f}',
            },
        }],
        'payment_source': {
            'paypal': {
                'experience_context': {
                    'brand_name': (brand_name or 'Store')[:127],
                    'shipping_preference': 'NO_SHIPPING',
                    'user_action': 'PAY_NOW',
                },
            },
        },
    }
    data = _api(site, '/v2/checkout/orders', method='POST', data=payload,
                request_id=f'create-{order.order_number}-{order.pay_amount}')
    return data.get('id', ''), data


def get_order(site, paypal_order_id):
    return _api(site, f'/v2/checkout/orders/{paypal_order_id}')


def capture_order(site, paypal_order_id):
    try:
        return _api(site, f'/v2/checkout/orders/{paypal_order_id}/capture', method='POST',
                    data={}, request_id=f'capture-{paypal_order_id}')
    except PayPalError as exc:
        issues = [d.get('issue') for d in exc.payload.get('details', [])]
        if 'ORDER_ALREADY_CAPTURED' in issues:
            return get_order(site, paypal_order_id)
        raise


def completed_capture(data):
    """Return (capture_id, amount, currency, payer_email) when the payment went through."""
    if data.get('status') != 'COMPLETED':
        return None
    for unit in data.get('purchase_units', []):
        for capture in unit.get('payments', {}).get('captures', []):
            if capture.get('status') == 'COMPLETED':
                amount = capture.get('amount', {})
                payer = data.get('payer', {}) or {}
                return (
                    capture.get('id', ''),
                    Decimal(amount.get('value', '0')),
                    amount.get('currency_code', ''),
                    payer.get('email_address', ''),
                )
    return None
